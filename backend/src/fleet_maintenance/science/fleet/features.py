"""Past-only feature engineering for fleet component health (docs/plan.md sections 4 and 16).

Every feature for day ``d`` uses readings up to and including ``d`` from the currently installed
part instance. ``test_fleet_features`` asserts that changing later readings leaves earlier
features untouched.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fleet_maintenance.science.fleet.catalog import COMPONENT_TYPES, MAX_PARAMETERS
from fleet_maintenance.science.fleet.simulator import FLAG_MISSING, FLAG_NO_FLIGHT, FLAG_OK, World

FLAG_STUCK = 2
FLAG_SPIKE = 3
PER_PARAMETER = ("z_now", "mean5", "mean20", "std5", "slope20", "dev")
FEATURE_NAMES: tuple[str, ...] = (
    *(f"p{k}_{name}" for k in range(MAX_PARAMETERS) for name in PER_PARAMETER),
    "zpos_max",
    "zpos_mean",
    "hours_since_install",
    "age_ratio",
    "faults_30d",
    "days_since_reading",
    "missing_rate_20",
    "cleaned_rate_20",
    "criticality",
    "type_index",
    "utilisation_30d",
    "ambient_20d",
)
FEATURE_INDEX = {name: index for index, name in enumerate(FEATURE_NAMES)}
TYPE_FEATURE = FEATURE_INDEX["type_index"]
HI_SCALE = 20.0  # z-units of combined deviation that map to health index 0


@dataclass
class Normaliser:
    """Per component type and parameter: reading ~ a + b * ambient + c * load, plus residual sd."""

    coefficients: np.ndarray  # (types, MAX_PARAMETERS, 3)
    residual_sd: np.ndarray  # (types, MAX_PARAMETERS)


@dataclass
class FeatureSet:
    values: np.ndarray  # (slots, days, features) float32
    has_reading: np.ndarray  # (slots, days) bool
    z: np.ndarray  # (slots, days, MAX_PARAMETERS) float32 cleaned normalised deviation
    clean_flags: np.ndarray  # (slots, days, MAX_PARAMETERS) uint8
    health_index: np.ndarray  # (slots, days) float32 0..100


def clean_readings(world: World) -> tuple[np.ndarray, np.ndarray]:
    """Flag stuck values (three identical consecutive readings) and spikes, using past data only."""
    values = world.readings.astype(np.float64).copy()
    flags = world.flags.copy()
    noise = np.array(
        [[p.noise for p in t.parameters] + [np.nan] * (MAX_PARAMETERS - len(t.parameters))
         for t in COMPONENT_TYPES]
    )[world.slot_type]
    slots, days, _ = values.shape
    for slot in range(slots):
        for k in range(MAX_PARAMETERS):
            if np.isnan(noise[slot, k]):
                continue
            series = values[slot, :, k]
            valid = np.flatnonzero(~np.isnan(series))
            if valid.size < 3:
                continue
            observed = series[valid]
            same = np.zeros(valid.size, dtype=bool)
            same[2:] = (observed[2:] == observed[1:-1]) & (observed[1:-1] == observed[:-2])
            history = np.full(valid.size, np.nan)
            spread = np.zeros(valid.size)
            if valid.size > 9:
                windows = np.lib.stride_tricks.sliding_window_view(observed[:-1], 9)
                history[9:] = np.median(windows, axis=1)
                spread[9:] = 1.4826 * np.median(np.abs(windows - history[9:, None]), axis=1)
            threshold = np.maximum(6.0 * noise[slot, k], 6.0 * spread)
            spike = np.abs(observed - history) > threshold
            spike &= ~np.isnan(history)
            flags[slot, valid[same], k] = FLAG_STUCK
            flags[slot, valid[spike & ~same], k] = FLAG_SPIKE
            series[valid[same | spike]] = np.nan
    return values, flags


def fit_normaliser(world: World, values: np.ndarray, train_mask: np.ndarray) -> Normaliser:
    """Fit operating-condition baselines on early-life training readings only."""
    types = len(COMPONENT_TYPES)
    coefficients = np.zeros((types, MAX_PARAMETERS, 3))
    residual_sd = np.ones((types, MAX_PARAMETERS))
    ambient = world.ambient[world.slot_aircraft]
    load = world.load_factor[world.slot_aircraft]
    life = np.array([t.mean_life_fh for t in COMPONENT_TYPES])[world.slot_type]
    early = world.hours_since_install < 0.35 * life[:, None] * world.config.life_scale
    for type_index, component_type in enumerate(COMPONENT_TYPES):
        rows = (world.slot_type == type_index)[:, None] & train_mask & early
        for k in range(len(component_type.parameters)):
            y = values[:, :, k][rows]
            keep = ~np.isnan(y)
            design = np.column_stack(
                [np.ones(keep.sum()), ambient[rows][keep] - 15.0, load[rows][keep] - 0.7]
            )
            solution, *_ = np.linalg.lstsq(design, y[keep], rcond=None)
            residual = y[keep] - design @ solution
            coefficients[type_index, k] = solution
            residual_sd[type_index, k] = max(float(np.std(residual)), 1e-6)
    return Normaliser(coefficients, residual_sd)


def _rolling(observed: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    count = np.arange(1, observed.size + 1)
    cumulative = np.concatenate([[0.0], np.cumsum(observed)])
    squares = np.concatenate([[0.0], np.cumsum(observed**2)])
    lower = np.maximum(count - window, 0)
    n = count - lower
    mean = (cumulative[count] - cumulative[lower]) / n
    variance = (squares[count] - squares[lower]) / n - mean**2
    return mean, np.sqrt(np.maximum(variance, 0.0))


def _rolling_slope(observed: np.ndarray, window: int) -> np.ndarray:
    """Least-squares slope per reading over the trailing window (at least five readings)."""
    index = np.arange(observed.size, dtype=np.float64)

    def trailing(series: np.ndarray) -> np.ndarray:
        cumulative = np.concatenate([[0.0], np.cumsum(series)])
        upper = np.arange(1, series.size + 1)
        totals: np.ndarray = cumulative[upper] - cumulative[np.maximum(upper - window, 0)]
        return totals

    n = np.minimum(index + 1, window)
    sx, sy = trailing(index), trailing(observed)
    sxx, sxy = trailing(index**2), trailing(index * observed)
    denominator = n * sxx - sx**2
    with np.errstate(divide="ignore", invalid="ignore"):
        slope = (n * sxy - sx * sy) / denominator
    return np.where(n >= 5, slope, np.nan)


def health_index(zpos_max: np.ndarray, zpos_mean: np.ndarray) -> np.ndarray:
    combined = 0.6 * zpos_max + 0.4 * zpos_mean
    return (100.0 * np.clip(1.0 - combined / HI_SCALE, 0.0, 1.0)).astype(np.float32)


def build_features(world: World, values: np.ndarray, flags: np.ndarray,
                   normaliser: Normaliser) -> FeatureSet:  # noqa: C901 - explicit vectorised steps
    slots, days, _ = values.shape
    precursor_days = np.zeros((slots, days), dtype=np.float32)
    for event in world.faults:
        if event.severity < 4:
            precursor_days[event.slot, event.day] += 1
    ambient = world.ambient[world.slot_aircraft]
    load = world.load_factor[world.slot_aircraft]
    coefficients = normaliser.coefficients[world.slot_type]  # (slots, K, 3)
    expected = (
        coefficients[:, None, :, 0]
        + coefficients[:, None, :, 1] * (ambient - 15.0)[:, :, None]
        + coefficients[:, None, :, 2] * (load - 0.7)[:, :, None]
    )
    direction = np.array(
        [[p.direction for p in t.parameters] + [0] * (MAX_PARAMETERS - len(t.parameters))
         for t in COMPONENT_TYPES]
    )[world.slot_type]
    z = direction[:, None, :] * (values - expected) / normaliser.residual_sd[world.slot_type][
        :, None, :
    ]
    feature = np.full((slots, days, len(FEATURE_NAMES)), np.nan, dtype=np.float32)
    has_reading = (flags == FLAG_OK).any(axis=2)
    instance = world.instance_index
    for slot in range(slots):
        boundaries = np.flatnonzero(np.diff(instance[slot])) + 1
        for segment in np.split(np.arange(days), boundaries):
            for k in range(MAX_PARAMETERS):
                if direction[slot, k] == 0:
                    continue
                series = z[slot, segment, k]
                valid = np.flatnonzero(~np.isnan(series))
                if valid.size == 0:
                    continue
                observed = series[valid]
                mean5, std5 = _rolling(observed, 5)
                mean20, _ = _rolling(observed, 20)
                slope20 = _rolling_slope(observed, 20)
                own = observed[:20].mean() if observed.size >= 20 else np.nan
                dev = np.where(np.arange(observed.size) >= 19, mean20 - own, np.nan)
                position = np.searchsorted(valid, np.arange(segment.size), side="right") - 1
                seen = position >= 0
                rows = segment[seen]
                index = position[seen]
                base = k * len(PER_PARAMETER)
                feature[slot, rows, base + 0] = observed[index]
                feature[slot, rows, base + 1] = mean5[index]
                feature[slot, rows, base + 2] = mean20[index]
                feature[slot, rows, base + 3] = std5[index]
                feature[slot, rows, base + 4] = slope20[index]
                feature[slot, rows, base + 5] = dev[index]
            # Days since the latest reading of this instance.
            reading_days = np.flatnonzero(has_reading[slot, segment])
            local = np.arange(segment.size)
            if reading_days.size:
                position = np.searchsorted(reading_days, local, side="right") - 1
                since = np.where(position >= 0, local - reading_days[np.maximum(position, 0)],
                                 local + 1)
            else:
                since = local + 1
            feature[slot, segment, FEATURE_INDEX["days_since_reading"]] = np.minimum(since, 60)
            # Precursor fault messages in the last 30 days for this instance.
            within = np.cumsum(precursor_days[slot, segment])
            lagged = np.concatenate([np.zeros(30), within[:-30]])[: segment.size]
            feature[slot, segment, FEATURE_INDEX["faults_30d"]] = within - lagged

    mean5 = feature[:, :, [k * len(PER_PARAMETER) + 1 for k in range(MAX_PARAMETERS)]]
    positive = np.maximum(np.nan_to_num(mean5, nan=0.0), 0.0)
    counts = np.maximum((direction != 0).sum(axis=1), 1)[:, None]
    feature[:, :, FEATURE_INDEX["zpos_max"]] = positive.max(axis=2)
    feature[:, :, FEATURE_INDEX["zpos_mean"]] = positive.sum(axis=2) / counts
    life = np.array([t.mean_life_fh for t in COMPONENT_TYPES])[world.slot_type]
    feature[:, :, FEATURE_INDEX["hours_since_install"]] = world.hours_since_install
    feature[:, :, FEATURE_INDEX["age_ratio"]] = world.hours_since_install / (
        life[:, None] * world.config.life_scale
    )
    flew = (flags != FLAG_NO_FLIGHT).any(axis=2)
    missing = (flags == FLAG_MISSING).any(axis=2) & flew
    cleaned = ((flags == FLAG_STUCK) | (flags == FLAG_SPIKE)).any(axis=2)
    feature[:, :, FEATURE_INDEX["missing_rate_20"]] = _trailing_rate(missing, flew, 20)
    feature[:, :, FEATURE_INDEX["cleaned_rate_20"]] = _trailing_rate(cleaned, flew, 20)
    feature[:, :, FEATURE_INDEX["criticality"]] = np.array(
        [t.criticality for t in COMPONENT_TYPES]
    )[world.slot_type][:, None]
    feature[:, :, TYPE_FEATURE] = world.slot_type[:, None]
    utilisation = _trailing_sum(world.flight_hours, 30)
    feature[:, :, FEATURE_INDEX["utilisation_30d"]] = utilisation[world.slot_aircraft]
    feature[:, :, FEATURE_INDEX["ambient_20d"]] = (
        _trailing_sum(world.ambient, 20) / 20.0
    )[world.slot_aircraft]
    hi = health_index(
        feature[:, :, FEATURE_INDEX["zpos_max"]], feature[:, :, FEATURE_INDEX["zpos_mean"]]
    )
    return FeatureSet(feature, has_reading, z.astype(np.float32), flags, hi)


def _trailing_sum(values: np.ndarray, window: int) -> np.ndarray:
    cumulative = np.cumsum(values, axis=1, dtype=np.float64)
    lagged = np.concatenate(
        [np.zeros((values.shape[0], window)), cumulative[:, :-window]], axis=1
    )
    totals: np.ndarray = (cumulative - lagged).astype(np.float32)
    return totals


def _trailing_rate(event: np.ndarray, base: np.ndarray, window: int) -> np.ndarray:
    events = _trailing_sum(event.astype(np.float32), window)
    bases = _trailing_sum(base.astype(np.float32), window)
    return np.where(bases > 0, events / np.maximum(bases, 1.0), 0.0).astype(np.float32)
