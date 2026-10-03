import random
from dataclasses import dataclass


@dataclass(frozen=True)
class EngineSplit:
    fit: tuple[str, ...]
    validation: tuple[str, ...]
    calibration: tuple[str, ...]


def split_engines(engine_ids: list[str], seed: int = 26249) -> EngineSplit:
    unique = sorted(set(engine_ids))
    if len(unique) != len(engine_ids):
        raise ValueError("Engine identities must be unique before splitting.")
    shuffled = unique[:]
    random.Random(seed).shuffle(shuffled)
    fit_end = round(len(shuffled) * 0.70)
    validation_end = fit_end + round(len(shuffled) * 0.15)
    return EngineSplit(
        tuple(sorted(shuffled[:fit_end])),
        tuple(sorted(shuffled[fit_end:validation_end])),
        tuple(sorted(shuffled[validation_end:])),
    )


def assert_disjoint(split: EngineSplit) -> None:
    groups = [set(split.fit), set(split.validation), set(split.calibration)]
    if any(groups[i] & groups[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("Engine partitions overlap.")
