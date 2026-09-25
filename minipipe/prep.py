"""Масштабирование и перемешивание признаков."""

import logging

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

Floats = NDArray[np.float64]


def minmax_scale(values: Floats) -> Floats:
    """Сжать значения в [0, 1]. Постоянная колонка даёт нули."""
    low = float(values.min())
    high = float(values.max())

    if high == low:
        logger.warning("колонка постоянна (%s), minmax вернёт нули", low)
        return np.zeros_like(values)

    logger.debug("minmax_scale: min=%s max=%s n=%d", low, high, len(values))
    return (values - low) / (high - low)


def standardize(values: Floats) -> Floats:
    """Привести к среднему 0 и разбросу 1."""
    mean = float(values.mean())
    spread = float(values.std())

    if spread == 0:
        logger.warning("нулевой разброс, standardize вернёт нули")
        return np.zeros_like(values)

    logger.debug("standardize: mean=%s std=%s", mean, spread)
    return (values - mean) / spread


def shuffled(values: Floats, seed: int = 0) -> Floats:
    """Копия массива в случайном порядке. Один seed — один результат."""
    generator = np.random.default_rng(seed)
    order = generator.permutation(len(values))
    logger.debug("shuffled: n=%d seed=%d", len(values), seed)
    return values[order]
