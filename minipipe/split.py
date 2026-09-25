"""Разделение выборки на train и test."""

import logging

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

Floats = NDArray[np.float64]
Labels = NDArray[np.int64]


def train_test_split(
    features: Floats,
    labels: Labels,
    test_size: float = 0.25,
    seed: int = 0,
) -> tuple[Floats, Floats, Labels, Labels]:
    """Перемешать и разрезать. Части не пересекаются и дают всю выборку."""
    if len(features) != len(labels):
        msg = f"признаков {len(features)}, меток {len(labels)} — должно быть поровну"
        raise ValueError(msg)
    if not 0.0 <= test_size <= 1.0:
        msg = f"test_size должен быть в [0, 1], пришло {test_size}"
        raise ValueError(msg)

    total = len(features)
    n_test = int(total * test_size)

    generator = np.random.default_rng(seed)
    order = generator.permutation(total)

    test_index = order[:n_test]
    train_index = order[n_test:]

    logger.info(
        "split: всего=%d train=%d test=%d seed=%d",
        total,
        len(train_index),
        len(test_index),
        seed,
    )

    return (
        features[train_index],
        features[test_index],
        labels[train_index],
        labels[test_index],
    )
