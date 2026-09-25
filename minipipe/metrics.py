"""Метрики бинарной классификации."""

import logging

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

Labels = NDArray[np.int64]


def _check_same_length(y_true: Labels, y_pred: Labels) -> None:
    if len(y_true) != len(y_pred):
        msg = f"истинных меток {len(y_true)}, предсказанных {len(y_pred)}"
        raise ValueError(msg)


def accuracy(y_true: Labels, y_pred: Labels) -> float:
    """Доля совпавших меток, всегда в [0, 1]. Пустая выборка — 0."""
    _check_same_length(y_true, y_pred)
    if len(y_true) == 0:
        logger.warning("пустая выборка, accuracy считаем нулём")
        return 0.0

    hits = int((y_true == y_pred).sum())
    logger.debug("accuracy: попаданий %d из %d", hits, len(y_true))
    return hits / len(y_true)


def confusion_counts(y_true: Labels, y_pred: Labels) -> tuple[int, int, int, int]:
    """Для меток 0/1: (tp, fp, tn, fn). Сумма равна размеру выборки."""
    _check_same_length(y_true, y_pred)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    logger.debug("confusion: tp=%d fp=%d tn=%d fn=%d", tp, fp, tn, fn)
    return tp, fp, tn, fn
