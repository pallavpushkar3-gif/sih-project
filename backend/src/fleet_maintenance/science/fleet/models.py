"""Anomaly, failure-risk and remaining-useful-life models (docs/plan.md section 4).

Substitutions against the plan, chosen to stay within the locked dependency set:
* LightGBM -> scikit-learn ``HistGradientBoosting*`` (same family of histogram GBDT).
* SHAP -> occlusion attribution on calibrated risk (replace a feature group by its healthy
  training median and measure the change). It describes model behaviour, not mechanical cause.

Splits are temporal and grouped by aircraft: held-out aircraft never contribute training rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import numpy as np
from sklearn.ensemble import (  # type: ignore[import-untyped]
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    IsolationForest,
)
from sklearn.isotonic import IsotonicRegression  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.metrics import (  # type: ignore[import-untyped]
    average_precision_score,
    brier_score_loss,
    precision_recall_curve,
)
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

from fleet_maintenance.science.fleet.catalog import COMPONENT_TYPES, MAX_PARAMETERS
from fleet_maintenance.science.fleet.features import (
    FEATURE_INDEX,
    FEATURE_NAMES,
    PER_PARAMETER,
    TYPE_FEATURE,
    FeatureSet,
)
from fleet_maintenance.science.fleet.simulator import World

RUL_CAP_DAYS = 60
RISK_HORIZONS = (14, 30)
ANOMALY_COLUMNS = [
    FEATURE_INDEX[f"p{k}_{name}"]
    for k in range(MAX_PARAMETERS)
    for name in ("mean5", "std5", "slope20", "dev")
]
ANOMALY_PERCENTILE = 0.99
SUSTAINED_READINGS = 3


@dataclass(frozen=True)
class Split:
    train_end: date
    validation_end: date
    test_end: date
    held_out_aircraft: tuple[str, ...]

    def periods(self, world: World) -> dict[str, tuple[int, int]]:
        def day(value: date) -> int:
            return (value - world.start).days

        return {
            "train": (0, day(self.train_end)),
            "validation": (day(self.train_end), day(self.validation_end)),
            "test": (day(self.validation_end), day(self.test_end)),
            "live": (day(self.test_end), world.days),
        }


@dataclass
class Labels:
    rul: np.ndarray  # (slots, days) float32 days to failure, capped; nan when unknown
    fail: dict[int, np.ndarray]  # horizon -> (slots, days) float32 1/0, nan when unknown


@dataclass
class TrainedModels:
    anomaly: IsolationForest
    anomaly_reference: np.ndarray  # sorted training anomaly scores for percentile mapping
    risk: dict[int, HistGradientBoostingClassifier]
    risk_calibration: dict[int, IsotonicRegression]
    risk_baseline: LogisticRegression
    risk_baseline_scaler: StandardScaler
    risk_baseline_calibration: IsotonicRegression
    rul: dict[float, HistGradientBoostingRegressor]
    rul_conformal: dict[str, float]  # bucket -> interval widening in days (validation CQR)
    reference_values: np.ndarray  # healthy training medians for occlusion attribution
    anomaly_threshold: float = ANOMALY_PERCENTILE
    evaluation: dict[str, object] = field(default_factory=dict)


def default_split(world: World) -> Split:
    rng = np.random.default_rng(world.config.seed + 7)
    held_out = sorted(rng.choice(world.aircraft_ids, size=8, replace=False).tolist())
    as_of = world.config.as_of
    return Split(
        train_end=date(as_of.year - 1, 10, 1),
        validation_end=date(as_of.year, 2, 1),
        test_end=as_of - timedelta(days=world.config.live_unlabelled_days - 1),
        held_out_aircraft=tuple(held_out),
    )


def build_labels(world: World) -> Labels:
    """Labels come from recorded failure events and removals; hidden health is never used."""
    slots, days = world.slots, world.days
    rul = np.full((slots, days), np.nan, dtype=np.float32)
    fail = {h: np.full((slots, days), np.nan, dtype=np.float32) for h in RISK_HORIZONS}
    failures = {(slot, day) for slot, day, _ in world.truth.failure_days}
    by_slot: dict[int, list[tuple[int, int | None, bool]]] = {}
    for instance in world.instances:
        failed_day = None
        if instance.removed is not None and instance.removal_reason == "unscheduled":
            failed_day = next(
                (day for day in range(instance.installed, instance.removed + 1)
                 if (instance.slot, day) in failures),
                None,
            )
        by_slot.setdefault(instance.slot, []).append(
            (instance.installed, instance.removed, failed_day is not None)
        )
        days_range = np.arange(instance.installed, (instance.removed or days - 1) + 1)
        days_range = days_range[days_range < days]
        if failed_day is not None:
            remaining = failed_day - days_range
            usable = remaining >= 0
            rul[instance.slot, days_range[usable]] = np.minimum(remaining[usable], RUL_CAP_DAYS)
            for horizon in RISK_HORIZONS:
                fail[horizon][instance.slot, days_range[usable]] = remaining[usable] <= horizon
        else:
            end = instance.removed if instance.removed is not None else days - 1
            remaining = end - days_range
            rul[instance.slot, days_range[remaining > RUL_CAP_DAYS]] = RUL_CAP_DAYS
            for horizon in RISK_HORIZONS:
                fail[horizon][instance.slot, days_range[remaining > horizon]] = 0.0
    return Labels(rul, fail)


def _rows(
    world: World, features: FeatureSet, split: Split, period: str, held_out: bool | None
) -> tuple[np.ndarray, np.ndarray]:
    start, end = split.periods(world)[period]
    held = np.isin(np.array(world.aircraft_ids), split.held_out_aircraft)[world.slot_aircraft]
    mask = np.zeros((world.slots, world.days), dtype=bool)
    mask[:, start:end] = True
    mask &= features.has_reading
    if held_out is True:
        mask &= held[:, None]
    elif held_out is False:
        mask &= ~held[:, None]
    return np.nonzero(mask)


def _matrix(features: FeatureSet, rows: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    matrix: np.ndarray = features.values[rows[0], rows[1]].astype(np.float64)
    return matrix


def anomaly_matrix(x: np.ndarray) -> np.ndarray:
    matrix: np.ndarray = np.nan_to_num(x[:, ANOMALY_COLUMNS], nan=0.0)
    return matrix


def anomaly_percentile(models: TrainedModels, x: np.ndarray) -> np.ndarray:
    raw = -models.anomaly.score_samples(anomaly_matrix(x))
    percentile: np.ndarray = (
        np.searchsorted(models.anomaly_reference, raw) / models.anomaly_reference.size
    )
    return percentile


def predict_risk(models: TrainedModels, x: np.ndarray, horizon: int) -> np.ndarray:
    raw = models.risk[horizon].predict_proba(x)[:, 1]
    calibrated: np.ndarray = np.clip(models.risk_calibration[horizon].predict(raw), 0.0, 1.0)
    return calibrated


def _raw_rul(rul: dict[float, HistGradientBoostingRegressor], x: np.ndarray) -> np.ndarray:
    quantiles: np.ndarray = np.sort(
        np.column_stack([rul[q].predict(x) for q in (0.1, 0.5, 0.9)]), axis=1
    )
    return quantiles


def _bucket(median: np.ndarray) -> np.ndarray:
    buckets: np.ndarray = np.where(median < 45.0, "near", "far")
    return buckets


def predict_rul(models: TrainedModels, x: np.ndarray) -> np.ndarray:
    """10/50/90 quantiles, with the interval widened by split-conformal calibration."""
    quantiles = _raw_rul(models.rul, x)
    widen = np.array([models.rul_conformal[b] for b in _bucket(quantiles[:, 1])])
    quantiles[:, 0] -= widen
    quantiles[:, 2] += widen
    clipped: np.ndarray = np.clip(quantiles, 0.0, RUL_CAP_DAYS)
    return clipped


def train(world: World, features: FeatureSet, labels: Labels, split: Split) -> TrainedModels:
    rng = np.random.default_rng(world.config.seed + 11)
    train_rows = _rows(world, features, split, "train", held_out=False)
    validation_rows = _rows(world, features, split, "validation", held_out=False)
    x_train = _matrix(features, train_rows)
    x_validation = _matrix(features, validation_rows)

    # A. Anomaly detection: Isolation Forest on residual statistics.
    sample = rng.choice(x_train.shape[0], size=min(60000, x_train.shape[0]), replace=False)
    anomaly = IsolationForest(n_estimators=150, max_samples=4096, random_state=world.config.seed)
    anomaly.fit(anomaly_matrix(x_train[sample]))
    reference = np.sort(-anomaly.score_samples(anomaly_matrix(x_train[sample])))

    # B. Failure risk for 14 and 30 days: gradient boosting with isotonic calibration.
    risk: dict[int, HistGradientBoostingClassifier] = {}
    calibration: dict[int, IsotonicRegression] = {}
    for horizon in RISK_HORIZONS:
        y = labels.fail[horizon][train_rows]
        known = ~np.isnan(y)
        positive = known & (y == 1)
        negative = np.flatnonzero(known & (y == 0))
        keep_negative = rng.choice(negative, size=min(negative.size, 120000), replace=False)
        chosen = np.concatenate([np.flatnonzero(positive), keep_negative])
        weights = np.where(y[chosen] == 1, 1.0, negative.size / keep_negative.size)
        model = HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.07, max_leaf_nodes=31, l2_regularization=1.0,
            categorical_features=[TYPE_FEATURE], random_state=world.config.seed,
        )
        model.fit(x_train[chosen], y[chosen], sample_weight=weights)
        y_validation = labels.fail[horizon][validation_rows]
        known_validation = ~np.isnan(y_validation)
        isotonic = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        isotonic.fit(
            model.predict_proba(x_validation[known_validation])[:, 1],
            y_validation[known_validation],
        )
        risk[horizon], calibration[horizon] = model, isotonic

    # Baseline for B: logistic regression on standardised features (14-day horizon).
    y = labels.fail[14][train_rows]
    known = np.flatnonzero(~np.isnan(y))
    pick = rng.choice(known, size=min(known.size, 150000), replace=False)
    scaler = StandardScaler().fit(np.nan_to_num(x_train[pick]))
    baseline = LogisticRegression(max_iter=400, class_weight="balanced")
    baseline.fit(scaler.transform(np.nan_to_num(x_train[pick])), y[pick])
    y_validation = labels.fail[14][validation_rows]
    known_validation = ~np.isnan(y_validation)
    baseline_isotonic = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    baseline_isotonic.fit(
        baseline.predict_proba(
            scaler.transform(np.nan_to_num(x_validation[known_validation]))
        )[:, 1],
        y_validation[known_validation],
    )

    # C. RUL: quantile gradient boosting on the capped target.
    y_rul = labels.rul[train_rows]
    known_rul = np.flatnonzero(~np.isnan(y_rul))
    near = known_rul[y_rul[known_rul] < RUL_CAP_DAYS]
    far = known_rul[y_rul[known_rul] >= RUL_CAP_DAYS]
    far = rng.choice(far, size=min(far.size, 4 * max(near.size, 1)), replace=False)
    chosen_rul = np.concatenate([near, far])
    rul_models = {}
    for quantile in (0.1, 0.5, 0.9):
        regressor = HistGradientBoostingRegressor(
            loss="quantile", quantile=quantile, max_iter=200, learning_rate=0.07,
            max_leaf_nodes=31, categorical_features=[TYPE_FEATURE],
            random_state=world.config.seed,
        )
        regressor.fit(x_train[chosen_rul], y_rul[chosen_rul])
        rul_models[quantile] = regressor

    # Conformalised quantile regression on validation rows: widen until ~80% coverage.
    y_validation_rul = labels.rul[validation_rows]
    known_validation_rul = ~np.isnan(y_validation_rul)
    raw_validation = _raw_rul(rul_models, x_validation[known_validation_rul])
    truth_validation = y_validation_rul[known_validation_rul]
    score = np.maximum(raw_validation[:, 0] - truth_validation,
                       truth_validation - raw_validation[:, 2])
    buckets = _bucket(raw_validation[:, 1])
    conformal = {}
    for bucket in ("near", "far"):
        inside = buckets == bucket
        conformal[bucket] = (
            max(0.0, float(np.quantile(score[inside], 0.8))) if inside.sum() >= 30 else 0.0
        )

    healthy = labels.fail[30][train_rows] == 0
    reference_values = np.nanmedian(x_train[healthy], axis=0)
    models = TrainedModels(
        anomaly=anomaly,
        anomaly_reference=reference,
        risk=risk,
        risk_calibration=calibration,
        risk_baseline=baseline,
        risk_baseline_scaler=scaler,
        risk_baseline_calibration=baseline_isotonic,
        rul=rul_models,
        rul_conformal=conformal,
        reference_values=reference_values,
    )
    models.anomaly_threshold = _select_anomaly_threshold(
        world, features, labels, split, models
    )
    return models


def _select_anomaly_threshold(world: World, features: FeatureSet, labels: Labels, split: Split,
                              models: TrainedModels) -> float:
    """Pick the percentile on validation data using recorded labels only (no hidden truth).

    Healthy rows are those with no recorded failure within 60 days. The rule maximises episodes
    flagged within 30 days before failure while keeping sustained alerts on healthy rows at or
    below 0.5 per 1,000.
    """
    rows = _rows(world, features, split, "validation", held_out=False)
    rng = np.random.default_rng(world.config.seed + 13)
    pick = np.sort(rng.choice(rows[0].size, size=min(40000, rows[0].size), replace=False))
    rows = (rows[0][pick], rows[1][pick])
    x = _matrix(features, rows)
    percentile = anomaly_percentile(models, x)
    residual = x[:, FEATURE_INDEX["zpos_max"]]
    rul = labels.rul[rows]
    healthy = rul >= RUL_CAP_DAYS
    approaching = rul <= 30
    best, best_recall = ANOMALY_PERCENTILE, -1.0
    for threshold in (0.95, 0.97, 0.98, 0.99, 0.995):
        flag = (percentile >= threshold) & (residual >= 2.0)
        false_rate = 1000 * (flag & healthy).sum() / max(healthy.sum(), 1)
        recall = (flag & approaching).sum() / max(approaching.sum(), 1)
        if false_rate <= 0.5 and recall > best_recall:
            best, best_recall = threshold, recall
    return best


def _recall_at_precision(y: np.ndarray, score: np.ndarray, precision: float) -> float:
    precisions, recalls, _ = precision_recall_curve(y, score)
    eligible = recalls[precisions >= precision]
    return float(eligible.max()) if eligible.size else 0.0


def _cmapss_score(error: np.ndarray) -> float:
    """Asymmetric score used in C-MAPSS work: late predictions (positive error) cost more."""
    return float(np.mean(np.where(error < 0, np.exp(-error / 13.0) - 1, np.exp(error / 10.0) - 1)))


def linear_rul_baseline(features: FeatureSet, rows: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    """Extrapolate the health index trend (last ~20 readings) to a threshold of 20."""
    hi = features.health_index
    current = hi[rows]
    past = hi[rows[0], np.maximum(rows[1] - 20, 0)]
    slope = (current - past) / 20.0
    with np.errstate(divide="ignore", invalid="ignore"):
        days = np.where(slope < -1e-3, (current - 20.0) / -slope, RUL_CAP_DAYS)
    return np.clip(days, 0.0, RUL_CAP_DAYS)


def evaluate(world: World, features: FeatureSet, labels: Labels, split: Split,
             models: TrainedModels) -> dict[str, object]:
    report: dict[str, object] = {
        "data": "synthetic",
        "split": {
            "train_end": split.train_end.isoformat(),
            "validation_end": split.validation_end.isoformat(),
            "test_end": split.test_end.isoformat(),
            "held_out_aircraft": list(split.held_out_aircraft),
            "grouping": "test metrics use the held-out aircraft in the test period",
        },
    }
    test_rows = _rows(world, features, split, "test", held_out=True)
    test_all = _rows(world, features, split, "test", held_out=None)
    x_test = _matrix(features, test_rows)

    risk_report: dict[str, object] = {}
    for horizon in RISK_HORIZONS:
        y = labels.fail[horizon][test_rows]
        known = ~np.isnan(y)
        score = predict_risk(models, x_test[known], horizon)
        entry: dict[str, Any] = {
            "rows": int(known.sum()),
            "positives": int(y[known].sum()),
            "base_rate": float(y[known].mean()),
            "pr_auc": float(average_precision_score(y[known], score)),
            "recall_at_precision_0_5": _recall_at_precision(y[known], score, 0.5),
            "brier": float(brier_score_loss(y[known], score)),
        }
        if horizon == 14:
            baseline_score = models.risk_baseline_calibration.predict(
                models.risk_baseline.predict_proba(
                    models.risk_baseline_scaler.transform(np.nan_to_num(x_test[known]))
                )[:, 1]
            )
            entry["baseline_logistic_pr_auc"] = float(
                average_precision_score(y[known], baseline_score)
            )
            entry["baseline_logistic_brier"] = float(brier_score_loss(y[known], baseline_score))
            entry["calibration_curve"] = _calibration_curve(y[known], score)
        risk_report[f"{horizon}d"] = entry
    report["failure_risk"] = risk_report

    y_rul = labels.rul[test_rows]
    known_rul = ~np.isnan(y_rul)
    prediction = predict_rul(models, x_test[known_rul])
    truth = y_rul[known_rul]
    near = truth < RUL_CAP_DAYS
    baseline = linear_rul_baseline(
        features, (test_rows[0][known_rul], test_rows[1][known_rul])
    )
    report["rul"] = {
        "rows": int(known_rul.sum()),
        "cap_days": RUL_CAP_DAYS,
        "mae_days": float(np.mean(np.abs(prediction[:, 1] - truth))),
        "mae_days_near_failure": float(np.mean(np.abs(prediction[near, 1] - truth[near]))),
        "baseline_linear_mae_days": float(np.mean(np.abs(baseline - truth))),
        "baseline_linear_mae_near_failure": float(np.mean(np.abs(baseline[near] - truth[near]))),
        "cmapss_score": _cmapss_score(prediction[near, 1] - truth[near]),
        "baseline_cmapss_score": _cmapss_score(baseline[near] - truth[near]),
        "interval_coverage_10_90": float(
            np.mean((truth >= prediction[:, 0]) & (truth <= prediction[:, 2]))
        ),
        "interval_coverage_near_failure": float(
            np.mean((truth[near] >= prediction[near, 0]) & (truth[near] <= prediction[near, 2]))
        ),
        "mean_interval_width_days": float(np.mean(prediction[:, 2] - prediction[:, 0])),
    }
    report["anomaly"] = _anomaly_report(world, features, split, models, test_all)
    report["lead_time"] = _risk_lead_time(world, features, split, models)
    return report


def _calibration_curve(y: np.ndarray, score: np.ndarray) -> list[dict[str, float]]:
    bins = np.linspace(0, 1, 11)
    points = []
    for low, high in zip(bins[:-1], bins[1:], strict=True):
        inside = (score >= low) & (score < high if high < 1 else score <= high)
        if inside.sum() >= 20:
            points.append(
                {"predicted": float(score[inside].mean()), "observed": float(y[inside].mean()),
                 "rows": int(inside.sum())}
            )
    return points


def sustained(flags: np.ndarray, readings: int = SUSTAINED_READINGS) -> np.ndarray:
    """True where a flag has held for ``readings`` consecutive observed rows (last axis)."""
    run = np.zeros(flags.shape, dtype=np.int32)
    current = np.zeros(flags.shape[:-1], dtype=np.int32)
    for j in range(flags.shape[-1]):
        current = np.where(flags[..., j], current + 1, 0)
        run[..., j] = current
    return run >= readings


def _anomaly_report(world: World, features: FeatureSet, split: Split, models: TrainedModels,
                    rows: tuple[np.ndarray, np.ndarray]) -> dict[str, object]:
    """Detection lead time and false alarms, evaluated with hidden truth (evaluation only)."""
    start, end = split.periods(world)["test"]
    x = _matrix(features, rows)
    percentile = anomaly_percentile(models, x)
    residual = x[:, FEATURE_INDEX["zpos_max"]]
    flag_model = np.zeros((world.slots, world.days), dtype=bool)
    flag_baseline = np.zeros((world.slots, world.days), dtype=bool)
    flag_model[rows] = (percentile >= models.anomaly_threshold) & (residual >= 2.0)
    flag_baseline[rows] = residual >= 3.0
    result: dict[str, object] = {"selected_percentile": models.anomaly_threshold}
    detectors = (("isolation_forest_residual", flag_model), ("rolling_z_baseline", flag_baseline))
    for name, flag in detectors:
        alert = np.zeros_like(flag)
        for slot in range(world.slots):
            observed = np.flatnonzero(features.has_reading[slot, start:end]) + start
            if observed.size:
                alert[slot, observed] = sustained(flag[slot, observed][None, :])[0]
        leads, detected, episodes = [], 0, 0
        for slot, day, sudden in world.truth.failure_days:
            if not start + 30 <= day < end or sudden:
                continue
            episodes += 1
            window = np.flatnonzero(alert[slot, max(start, day - 60): day + 1])
            if window.size:
                detected += 1
                leads.append(int(day - (max(start, day - 60) + window[0])))
        healthy = world.truth.health[rows] > 0.69
        false_alarms = alert[rows] & healthy
        result[name] = {
            "degradation_episodes": episodes,
            "episodes_detected": detected,
            "recall": detected / episodes if episodes else 0.0,
            "median_lead_time_days": float(np.median(leads)) if leads else 0.0,
            "false_alarms_per_1000_healthy_rows": float(
                1000 * false_alarms.sum() / max(healthy.sum(), 1)
            ),
        }
    return result


def _risk_lead_time(world: World, features: FeatureSet, split: Split,
                    models: TrainedModels) -> dict[str, object]:
    start, end = split.periods(world)["test"]
    leads = []
    missed = 0
    for slot, day, _sudden in world.truth.failure_days:
        if not start + 30 <= day < end:
            continue
        window = np.arange(max(start, day - 45), day + 1)
        window = window[features.has_reading[slot, window]]
        if not window.size:
            missed += 1
            continue
        risk = predict_risk(models, features.values[slot, window].astype(np.float64), 14)
        alarm = np.flatnonzero(risk >= 0.5)
        if alarm.size:
            leads.append(int(day - window[alarm[0]]))
        else:
            missed += 1
    return {
        "threshold": 0.5,
        "failures": len(leads) + missed,
        "warned": len(leads),
        "median_days_of_warning": float(np.median(leads)) if leads else 0.0,
        "lead_time_days": sorted(leads),
    }


GROUPS: dict[str, list[int]] = {
    "usage_and_age": [FEATURE_INDEX[name] for name in
                      ("hours_since_install", "age_ratio", "utilisation_30d")],
    "fault_messages": [FEATURE_INDEX["faults_30d"]],
    "data_quality": [FEATURE_INDEX[name] for name in
                     ("days_since_reading", "missing_rate_20", "cleaned_rate_20")],
    "operating_conditions": [FEATURE_INDEX["ambient_20d"]],
}


def _groups(type_index: int) -> dict[str, list[int]]:
    groups = dict(GROUPS)
    for k, parameter in enumerate(COMPONENT_TYPES[type_index].parameters):
        groups[f"parameter:{parameter.name}"] = [
            FEATURE_INDEX[f"p{k}_{name}"] for name in PER_PARAMETER
        ]
    return groups


def attribution_batch(models: TrainedModels, x: np.ndarray,
                      type_indices: np.ndarray) -> list[list[dict[str, Any]]]:
    """Occlusion attribution of the 14-day risk model's log-odds, for many rows at once.

    Each feature group is replaced by its healthy training median and the change in log-odds
    is reported. Log-odds keep attributions informative for low-risk components, where the
    calibrated probability is flat at zero. The result describes model behaviour, not cause.
    """
    model = models.risk[14]
    base = model.decision_function(x)
    variants: list[np.ndarray] = []
    owners: list[tuple[int, str]] = []
    for row, type_index in enumerate(type_indices):
        count = len(COMPONENT_TYPES[int(type_index)].parameters)
        mean5 = [FEATURE_INDEX[f"p{k}_mean5"] for k in range(count)]
        for name, columns in _groups(int(type_index)).items():
            variant = x[row].copy()
            variant[columns] = models.reference_values[columns]
            # Keep the combined deviation features consistent with the occluded parameter.
            positive = np.maximum(np.nan_to_num(variant[mean5], nan=0.0), 0.0)
            variant[FEATURE_INDEX["zpos_max"]] = positive.max()
            variant[FEATURE_INDEX["zpos_mean"]] = positive.sum() / max(count, 1)
            variants.append(variant)
            owners.append((row, name))
    occluded = model.decision_function(np.array(variants)) if variants else np.array([])
    result: list[list[dict[str, Any]]] = [[] for _ in range(x.shape[0])]
    for (row, name), value in zip(owners, occluded, strict=True):
        result[row].append({"factor": name, "contribution": float(base[row] - value)})
    return [sorted(rows, key=lambda item: -abs(float(item["contribution"]))) for rows in result]


def attribution(models: TrainedModels, x: np.ndarray, type_index: int) -> list[dict[str, Any]]:
    return attribution_batch(models, x[None, :], np.array([type_index]))[0]


__all__ = [
    "FEATURE_NAMES",
    "Labels",
    "Split",
    "TrainedModels",
    "anomaly_percentile",
    "attribution",
    "attribution_batch",
    "build_labels",
    "default_split",
    "evaluate",
    "predict_risk",
    "predict_rul",
    "train",
]
