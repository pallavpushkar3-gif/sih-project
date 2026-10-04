"""Final FD001 evaluation: explicit frozen policy, immutable model, engine-level metrics."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml  # type: ignore[import-untyped]
from scipy.stats import beta  # type: ignore[import-untyped]

from fleet_maintenance.science.data.features import SnapshotDataset, snapshot_features
from fleet_maintenance.science.data.loaders import load_cmapss_table, load_rul_labels
from fleet_maintenance.science.prediction.evaluation import regression_metrics
from fleet_maintenance.science.prediction.inference import BaselinePredictor


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class FinalEvaluationConfig:
    raw: Path
    artifact_dir: Path
    policy: Path
    output: Path


def evaluate_final(config: FinalEvaluationConfig) -> dict[str, object]:
    policy = yaml.safe_load(config.policy.read_text())
    if not policy["status"].startswith("frozen_demonstrator_targets"):
        raise ValueError("Final-test evaluation requires a frozen acceptance policy")
    predictor = BaselinePredictor.load(config.artifact_dir)
    calibration = json.loads((config.artifact_dir / "calibration.json").read_text())
    if calibration["model_artifacts"] != predictor.manifest["artifacts"]:
        raise ValueError("Calibration/model artifact hashes differ")
    test_path, labels_path = config.raw / "test_FD001.txt", config.raw / "RUL_FD001.txt"
    table = load_cmapss_table(test_path, "FD001", "test")
    engines = np.unique(table.engine_numbers)
    labels = load_rul_labels(labels_path, len(engines))
    values, identities, cutoffs, true_values = [], [], [], []
    withheld = []
    for engine, truth in zip(engines, labels, strict=True):
        mask = table.engine_numbers == engine
        history, cycles = table.features[mask], table.cycles[mask]
        identity = f"NASA_CMAPSS:FD001:test:{engine}"
        if len(history) < int(str(predictor.manifest["minimum_history_cycles"])):
            withheld.append(identity)
            continue
        cutoff = int(cycles[-1])
        values.append(
            snapshot_features(
                history, cutoff, int(str(predictor.manifest["feature_window_cycles"]))
            )
        )
        identities.append(identity)
        cutoffs.append(cutoff)
        true_values.append(float(truth))
    uncapped = np.asarray(true_values, dtype=np.float64)
    capped = np.minimum(uncapped, policy["target_cap_cycles"])
    dataset = SnapshotDataset(
        tuple(identities),
        np.asarray(cutoffs, dtype=np.int64),
        np.vstack(values),
        capped,
    )
    predictions = predictor.predict(dataset)
    quantile = float(calibration["diagnostic"]["residual_quantile_cycles"])
    lower, upper = np.maximum(predictions - quantile, 0), predictions + quantile
    coverage_mask = (capped >= lower) & (capped <= upper)
    successes, count = int(coverage_mask.sum()), len(capped)
    coverage = float(coverage_mask.mean())
    lower_confidence = float(beta.ppf(0.05, successes, count - successes + 1)) if successes else 0.0
    metrics = regression_metrics(capped, predictions).as_dict()
    generator = np.random.default_rng(26249)
    indices = generator.integers(0, count, size=(2000, count))
    errors = predictions - capped
    mae_samples = np.abs(errors[indices]).mean(axis=1)
    rmse_samples = np.sqrt(np.square(errors[indices]).mean(axis=1))
    widths = upper - lower
    gates = {
        "mae": metrics["mae_cycles"] <= policy["prediction"]["maximum_mae_cycles"],
        "rmse": metrics["rmse_cycles"] <= policy["prediction"]["maximum_rmse_cycles"],
        "coverage": coverage >= policy["intervals"]["minimum_empirical_coverage"],
        "coverage_confidence": lower_confidence
        >= policy["intervals"]["minimum_one_sided_95pct_coverage_lower_bound"],
        "mean_width": float(widths.mean()) <= policy["intervals"]["maximum_mean_width_cycles"],
        "no_withheld_engines": not withheld,
    }
    groups = []
    for name, mask in [
        ("0-20", uncapped <= 20),
        ("21-45", (uncapped > 20) & (uncapped <= 45)),
        ("46-125", (uncapped > 45) & (uncapped <= 125)),
        (">125", uncapped > 125),
    ]:
        groups.append(
            {
                "true_rul_band_cycles": name,
                "count": int(mask.sum()),
                "capped_coverage": float(coverage_mask[mask].mean()) if mask.any() else None,
                "mean_width_cycles": float(widths[mask].mean()) if mask.any() else None,
                "small_group": int(mask.sum()) < 30,
            }
        )
    payload = {
        "version": "final-fd001-v1",
        "label": "simulated FD001 final-test demonstrator evaluation",
        "policy_version": policy["version"],
        "policy_sha256": digest(config.policy),
        "model_manifest_sha256": digest(config.artifact_dir / "manifest.json"),
        "calibration_sha256": digest(config.artifact_dir / "calibration.json"),
        "model_artifacts": predictor.manifest["artifacts"],
        "source_hashes": {
            test_path.name: digest(test_path),
            labels_path.name: digest(labels_path),
        },
        "evaluation_script_sha256": digest(Path(__file__)),
        "sampling_unit": "one_last_observed_cutoff_per_official_test_engine",
        "target_cap_cycles": policy["target_cap_cycles"],
        "eligible_count": count,
        "withheld_engines": withheld,
        "capped_primary": metrics,
        "uncapped_secondary": regression_metrics(uncapped, predictions).as_dict(),
        "bootstrap_95pct": {
            "mae": np.quantile(mae_samples, [0.025, 0.975]).tolist(),
            "rmse": np.quantile(rmse_samples, [0.025, 0.975]).tolist(),
            "seed": 26249,
            "replications": 2000,
        },
        "intervals": {
            "nominal_coverage": calibration["diagnostic"]["nominal_coverage"],
            "covered_count": successes,
            "coverage": coverage,
            "one_sided_95pct_lower_bound": lower_confidence,
            "mean_width_cycles": float(widths.mean()),
            "median_width_cycles": float(np.median(widths)),
            "p90_width_cycles": float(np.quantile(widths, 0.9)),
            "life_stage_groups": groups,
        },
        "gates": gates,
        "acceptance": "passed_demonstrator_prediction_interval_gates"
        if all(gates.values())
        else "failed_demonstrator_prediction_interval_gates",
        "alerts_acceptance": "not_evaluated_independent_complete_failure_histories_required",
        "final_test_inspected": True,
        "retuning_permitted_under_this_test_claim": False,
        "predictions": [
            {
                "engine_id": identity,
                "cutoff_cycle": cutoff,
                "true_uncapped_cycles": truth,
                "estimate_cycles": prediction,
                "lower_cycles": low,
                "upper_cycles": high,
            }
            for identity, cutoff, truth, prediction, low, high in zip(
                identities,
                cutoffs,
                uncapped.tolist(),
                predictions.tolist(),
                lower.tolist(),
                upper.tolist(),
                strict=True,
            )
        ],
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if config.output.exists() and config.output.read_text() != encoded:
        raise ValueError(
            "Existing evaluation differs; use a new identified output to preserve history"
        )
    config.output.parent.mkdir(parents=True, exist_ok=True)
    config.output.write_text(encoded)
    return payload
