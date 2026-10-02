"""Пайплайн на minipipe. Отдаёт nan вместо результата.

Несколько показаний отравлены NaN. Какие именно — выбирается заново на
каждый запуск, из исходников не угадать.

Скрипт трогать нельзя. Запуск разбирается в README.md.
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import secrets

import numpy as np
from numpy.typing import NDArray

from minipipe import KMeans, standardize

TOTAL = 4_000
FEATURES = 5
POISONED = 3

Floats = NDArray[np.float64]


@dataclass
class Reading:
    """Одно показание датчика."""

    index: int
    sensor: str
    values: Floats


def to_row(reading: Reading) -> Floats:
    """Отдаёт значения показания в общую матрицу."""
    return reading.values


def make_readings() -> list[Reading]:
    generator = np.random.default_rng(secrets.randbelow(2**32))
    readings = [
        Reading(
            index=i, sensor=f"snr-{secrets.token_hex(3)}", values=generator.normal(0, 1, FEATURES)
        )
        for i in range(TOTAL)
    ]

    spoiled: list[tuple[int, str]] = []
    chosen: set[int] = set()
    while len(chosen) < POISONED:
        chosen.add(secrets.randbelow(TOTAL))
    for index in sorted(chosen):
        reading = readings[index]
        reading.values[secrets.randbelow(FEATURES)] = np.nan
        spoiled.append((reading.index, reading.sensor))

    _remember_truth(spoiled)
    return readings


def _remember_truth(spoiled: list[tuple[int, str]]) -> None:
    """Записывает ответ для верификатора. Не подсматривай, это неинтересно."""
    destination = os.environ.get("NAN_HUNT_TRUTH")
    if destination:
        Path(destination).write_text(json.dumps(spoiled), encoding="utf-8")


def build_matrix(readings: list[Reading]) -> Floats:
    return np.vstack([to_row(reading) for reading in readings])


def main() -> None:
    readings = make_readings()
    matrix = build_matrix(readings)

    scaled = np.column_stack([standardize(matrix[:, column]) for column in range(FEATURES)])
    model = KMeans(n_clusters=4, seed=1, max_steps=20).fit(scaled)

    print(f"кластеров: {model.n_clusters}, инерция: {model.inertia_}")
    if np.isnan(model.inertia_):
        msg = "инерция получилась nan — где-то в данных NaN"
        raise ValueError(msg)


if __name__ == "__main__":
    main()
