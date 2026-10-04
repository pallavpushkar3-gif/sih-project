"""Validation-only diagnostics for the deployed single-feature sensitivity method."""

import json
import platform
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import numpy as np
import yaml  # type: ignore[import-untyped]

from fleet_maintenance.artifacts.storage import sha256
from fleet_maintenance.science.data.features import build_snapshot_dataset
from fleet_maintenance.science.data.loaders import load_cmapss_table
from fleet_maintenance.science.prediction.explanations import feature_sensitivities
from fleet_maintenance.science.prediction.inference import BaselinePredictor


def evaluate_explanations(
    raw: Path, directory: Path, config_path: Path, output: Path
) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text())
    predictor = BaselinePredictor.load(directory)
    manifest = cast(dict[str, Any], predictor.manifest)
    ids = tuple(str(value) for value in manifest["validation_engines"])
    fit_ids = set(manifest["fit_engines"])
    if set(ids) & fit_ids or not ids:
        raise ValueError(
            "Explanation diagnostics require nonempty validation engines disjoint from fit"
        )
    table = load_cmapss_table(raw / "train_FD001.txt", "FD001", "train")
    dataset = build_snapshot_dataset(
        table,
        ids,
        minimum_history=int(str(manifest["minimum_history_cycles"])),
        window=int(str(manifest["feature_window_cycles"])),
        target_cap=125,
        sampling="one_seeded_cutoff_per_engine",
        seed=int(config["seed"]),
    )
    standardized = (dataset.values - np.asarray(predictor.standardizer.mean)) / np.asarray(
        predictor.standardizer.scale
    )
    # Constant fit features stay fixed; perturbing them would fabricate supported variation.
    fit_numbers = [int(identity.rsplit(":", 1)[1]) for identity in fit_ids]
    raw_variable = np.ptp(table.features[np.isin(table.engine_numbers, fit_numbers)], axis=0) > 0
    variable = np.tile(raw_variable, 3)
    variable = np.concatenate((variable, [False]))  # dataset cycle is not sensor noise
    generator = np.random.default_rng(int(config["seed"]))
    rows: list[dict[str, Any]] = []
    for identity, cutoff, vector in zip(
        dataset.engine_ids, dataset.cutoffs, standardized, strict=True
    ):
        original = feature_sensitivities(predictor.model.predict, vector)
        repeated = feature_sensitivities(predictor.model.predict, vector)
        estimate = float(predictor.model.predict(vector[None, :])[0])
        # Independent scalar calls verify the batched intervention contract.
        direct = []
        for index in range(len(vector)):
            altered = vector.copy()
            altered[index] = 0.0
            direct.append(estimate - float(predictor.model.predict(altered[None, :])[0]))
        top = set(np.argsort(-np.abs(original), kind="stable")[:10].tolist())
        probes = []
        for _ in range(int(config["perturbation"]["repetitions_per_engine"])):
            noise = generator.normal(
                0, float(config["perturbation"]["standard_deviation"]), vector.shape
            )
            changed = vector + noise * variable
            sensitivity = feature_sensitivities(predictor.model.predict, changed)
            changed_top = set(np.argsort(-np.abs(sensitivity), kind="stable")[:10].tolist())
            norm = float(np.linalg.norm(original) * np.linalg.norm(sensitivity))
            probes.append(
                {
                    "top_10_jaccard": len(top & changed_top) / len(top | changed_top),
                    "sensitivity_vector_cosine": float(
                        np.clip(original @ sensitivity / norm, -1.0, 1.0)
                    )
                    if norm
                    else None,
                    "mean_absolute_sensitivity_change_cycles": float(
                        np.mean(np.abs(original - sensitivity))
                    ),
                    "prediction_absolute_change_cycles": abs(
                        estimate - float(predictor.model.predict(changed[None, :])[0])
                    ),
                }
            )
        rows.append(
            {
                "engine_id": identity,
                "cutoff_cycle": int(cutoff),
                "repeat_max_difference_cycles": float(np.max(np.abs(original - repeated))),
                "intervention_max_error_cycles": float(np.max(np.abs(original - direct))),
                "perturbations": probes,
            }
        )
    names = list(rows[0]["perturbations"][0])
    summary: dict[str, Any] = {}
    for name in names:
        values = [
            probe[name] for row in rows for probe in row["perturbations"] if probe[name] is not None
        ]
        summary[name] = (
            {
                "count": len(values),
                "mean": float(np.mean(values)),
                "p05": float(np.quantile(values, 0.05)),
                "p95": float(np.quantile(values, 0.95)),
            }
            if values
            else {"count": 0}
        )
    result = {
        "version": config["version"],
        "acceptance": "diagnostic_only_no_validated_stability_threshold",
        "final_test_loaded": False,
        "configuration": config,
        "configuration_sha256": sha256(config_path),
        "evaluation_module_sha256": sha256(Path(__file__)),
        "explanation_module_sha256": sha256(Path(__file__).with_name("explanations.py")),
        "environment": {
            "python": platform.python_version(),
            "numpy": version("numpy"),
            "scikit_learn": version("scikit-learn"),
        },
        "model_manifest_sha256": sha256(directory / "manifest.json"),
        "model_artifacts": manifest["artifacts"],
        "training_file_sha256": sha256(raw / "train_FD001.txt"),
        "engine_count": len(rows),
        "max_repeat_difference_cycles": max(row["repeat_max_difference_cycles"] for row in rows),
        "max_intervention_error_cycles": max(row["intervention_max_error_cycles"] for row in rows),
        "summary": summary,
        "results": rows,
        "limitations": (
            "Validation diagnostics only. Engineered-feature perturbations are not physical "
            "sensor noise; correlated replacements may be off-distribution. "
            "No additive or causal fidelity claim."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return result
