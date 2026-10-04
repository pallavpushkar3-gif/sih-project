"""New engine-disjoint experiment; prior experiments are not relabelled as unseen."""

import json
import platform
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import numpy as np
import yaml  # type: ignore[import-untyped]

from fleet_maintenance.artifacts.storage import sha256, verify_hashes
from fleet_maintenance.science.alerts.evaluation import (
    AlertHistory,
    AlertObservation,
    evaluate_policy,
)
from fleet_maintenance.science.data.features import (
    SnapshotDataset,
    build_snapshot_dataset,
    snapshot_features,
)
from fleet_maintenance.science.data.loaders import load_cmapss_table
from fleet_maintenance.science.data.splitting import EngineSplit, assert_disjoint
from fleet_maintenance.science.prediction.calibration import calibrate_baseline
from fleet_maintenance.science.prediction.evaluation import regression_metrics
from fleet_maintenance.science.prediction.inference import BaselinePredictor
from fleet_maintenance.science.prediction.training import train_baseline
from fleet_maintenance.services.alert_policy import AlertPolicy


def run_experiment(raw: Path, directory: Path, config_path: Path, output: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text())
    if config["status"] != "frozen_internal_simulated_benchmark_not_operational_acceptance":
        raise ValueError("Freeze the internal evaluation protocol before running")
    if directory.exists():
        raise ValueError("Use a new artifact directory; previous evaluated models are immutable")
    table = load_cmapss_table(raw / "train_FD001.txt", "FD001", "train")
    ids = sorted(set(table.identities))
    random.Random(config["seed"]).shuffle(ids)
    size = config["partition_sizes"]
    if sum(size.values()) != len(ids):
        raise ValueError("Partition counts must cover the available physical engines exactly")
    fit_end = size["fit"]
    val_end = fit_end + size["validation"]
    cal_end = val_end + size["calibration"]
    split = EngineSplit(
        tuple(sorted(ids[:fit_end])),
        tuple(sorted(ids[fit_end:val_end])),
        tuple(sorted(ids[val_end:cal_end])),
    )
    held = tuple(sorted(ids[cal_end:]))
    assert_disjoint(split)
    if set(held) & (set(split.fit) | set(split.validation) | set(split.calibration)):
        raise ValueError("Lifecycle evaluation engines overlap training/selection/calibration")
    provenance = {
        "configuration_sha256": sha256(config_path),
        "training_source_sha256": sha256(raw / "train_FD001.txt"),
        "evaluation_code_sha256": sha256(Path(__file__)),
        "backend_lock_sha256": sha256(Path("backend/uv.lock")),
        "calculation_module_hashes": {
            name: sha256(Path("backend/src/fleet_maintenance") / name)
            for name in (
                "science/prediction/training.py",
                "science/prediction/calibration.py",
                "science/prediction/inference.py",
                "science/data/features.py",
                "science/alerts/evaluation.py",
                "services/alert_episodes.py",
                "services/alert_policy.py",
            )
        },
        "experiment": config["version"],
    }
    manifest = {
        **asdict(split),
        "lifecycle_evaluation": held,
        "provenance": provenance,
        "historically_unseen": False,
        "qualification": "held out from this retrained model; prior FD001 experiments "
        "used these engines. This is internal simulated evaluation, not a blind external study.",
    }
    # Retain the split before fitting; no evaluation outcomes are used to choose it.
    directory.mkdir(parents=True)
    (directory / "split.json").write_text(json.dumps(manifest, indent=2) + "\n")
    train_baseline(
        table,
        split,
        directory,
        target_cap=config["target_cap_cycles"],
        minimum_history=config["minimum_history_cycles"],
        window=config["feature_window_cycles"],
        seed=config["seed"],
        provenance=provenance,
    )
    calibration = calibrate_baseline(
        table,
        split,
        directory,
        nominal_coverage=config["nominal_interval_coverage"],
        seed=config["seed"],
        provenance=provenance,
    )
    predictor = BaselinePredictor.load(directory)
    snapshots = build_snapshot_dataset(
        table,
        held,
        minimum_history=config["minimum_history_cycles"],
        window=config["feature_window_cycles"],
        target_cap=config["target_cap_cycles"],
        sampling="one_seeded_cutoff_per_engine",
        seed=config["seed"],
    )
    predicted = predictor.predict(snapshots)
    # Fixed training-only constant predictor is a transparent simple comparison.
    fit = build_snapshot_dataset(
        table,
        split.fit,
        sampling="all",
        seed=config["seed"],
        minimum_history=config["minimum_history_cycles"],
        window=config["feature_window_cycles"],
        target_cap=config["target_cap_cycles"],
    )
    constant = np.full_like(predicted, fit.targets.mean())
    q = calibration.residual_quantile_cycles
    lower, upper = np.maximum(predicted - q, 0), predicted + q
    covered = (lower <= snapshots.targets) & (snapshots.targets <= upper)
    rng = np.random.default_rng(config["seed"])
    indices = rng.integers(0, len(held), size=(2000, len(held)))
    histories = []
    exposure = 0
    for identity in held:
        number = int(identity.rsplit(":", 1)[1])
        history = table.features[table.engine_numbers == number]
        end = len(history)
        cutoffs = list(
            range(
                config["minimum_history_cycles"],
                end + 1,
                config["evaluation"]["lifecycle_replay_stride_cycles"],
            )
        )
        if cutoffs[-1] != end:
            cutoffs.append(end)
        values = np.vstack(
            [
                snapshot_features(history[:cutoff], cutoff, config["feature_window_cycles"])
                for cutoff in cutoffs
            ]
        )
        prefixes = SnapshotDataset(
            tuple(identity for _ in cutoffs), np.asarray(cutoffs), values, np.zeros(len(cutoffs))
        )
        estimates = predictor.predict(prefixes)
        histories.append(
            AlertHistory(
                identity,
                tuple(
                    AlertObservation(f"{identity}:{cutoff}", cutoff, float(estimate))
                    for cutoff, estimate in zip(cutoffs, estimates, strict=True)
                ),
                end,
            )
        )
        exposure += end - cutoffs[0]
    sensitivity = []
    for warning in (30, 45, 60):
        policy = AlertPolicy(warning_cycles=warning, version=f"diagnostic-warning-{warning}")
        metrics = evaluate_policy(
            tuple(histories), policy, warning_horizon_cycles=45, hysteresis=True, episodes=True
        )
        sensitivity.append(
            {
                "warning_threshold_cycles": warning,
                **asdict(metrics),
                "false_episodes_per_1000_observed_engine_cycles": metrics.false_alert_episodes
                * 1000
                / exposure,
            }
        )
    groups = []
    for name, mask in (
        ("0-20", snapshots.targets <= 20),
        ("21-45", (snapshots.targets > 20) & (snapshots.targets <= 45)),
        ("46-125 capped", snapshots.targets > 45),
    ):
        groups.append(
            {
                "stage": name,
                "engines": int(mask.sum()),
                "coverage": float(covered[mask].mean()) if mask.any() else None,
                "small_group": int(mask.sum()) < 30,
            }
        )
    report: dict[str, Any] = {
        "version": config["version"],
        "configuration": config,
        "split": manifest,
        "split_sha256": sha256(directory / "split.json"),
        "python": platform.python_version(),
        "model_artifacts": predictor.manifest["artifacts"],
        "calibration_sha256": sha256(directory / "calibration.json"),
        "sampling_unit": "One engine at one seeded cutoff; marginal, not trajectory-wide",
        "prediction": regression_metrics(snapshots.targets, predicted).as_dict(),
        "constant_baseline": regression_metrics(snapshots.targets, constant).as_dict(),
        "interval_coverage": float(covered.mean()),
        "mean_interval_width_cycles": float((upper - lower).mean()),
        "engine_bootstrap_95pct": {
            "mae": np.quantile(
                np.abs(predicted - snapshots.targets)[indices].mean(axis=1), [0.025, 0.975]
            ).tolist(),
            "coverage": np.quantile(covered[indices].mean(axis=1), [0.025, 0.975]).tolist(),
            "replications": 2000,
        },
        "life_stage_groups": groups,
        "operating_group": "FD001 single simulated regime only",
        "causal_lifecycle_replay": {
            "engine_count": len(held),
            "exposure_cycles": exposure,
            "policy_sensitivity": sensitivity,
        },
        "official_endpoints": "Previously inspected endpoints are not lifecycle evidence",
        "promotion": "not promoted; existing selected model retained",
        "qualification": "Internal simulated benchmark; operational data/alert costs unavailable",
    }
    verify_hashes(directory, cast(dict[str, str], predictor.manifest["artifacts"]))
    (directory / "model_card.json").write_text(
        json.dumps(
            {
                "support": "NASA simulated FD001 engine histories, cycles, 30-cycle minimum",
                "target_cap_cycles": 125,
                "statistical_unit": report["sampling_unit"],
                "exchangeability": "No real-aircraft, conditional or trajectory-wide guarantee",
                "split_sha256": report["split_sha256"],
                "promotion": report["promotion"],
            },
            indent=2,
        )
        + "\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    return report
