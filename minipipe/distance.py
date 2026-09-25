"""Расстояния между точками."""

import logging

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

Floats = NDArray[np.float64]
MATRIX_NDIM = 2


def squared_distances(points: Floats, centers: Floats) -> Floats:
    """Квадраты расстояний: (n, d) и (k, d) -> (n, k)."""
    if points.ndim != MATRIX_NDIM or centers.ndim != MATRIX_NDIM:
        msg = f"ожидаю двумерные массивы, пришло {points.ndim}D и {centers.ndim}D"
        raise ValueError(msg)
    if points.shape[1] != centers.shape[1]:
        msg = f"размерности не совпадают: {points.shape[1]} и {centers.shape[1]}"
        raise ValueError(msg)

    logger.debug("distances: %d точек на %d центров", len(points), len(centers))
    difference = points[:, None, :] - centers[None, :, :]
    return (difference**2).sum(axis=2)
