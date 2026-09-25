"""k ближайших соседей, брутфорсом."""

from dataclasses import dataclass, field
import logging
from typing import Self

import numpy as np
from numpy.typing import NDArray

from minipipe.distance import squared_distances

logger = logging.getLogger(__name__)

Floats = NDArray[np.float64]
Labels = NDArray[np.int64]


@dataclass
class KNN:
    """Метка точки — большинство среди k ближайших соседей."""

    k: int = 3
    _features: Floats = field(default_factory=lambda: np.empty((0, 0)), repr=False)
    _labels: Labels = field(default_factory=lambda: np.empty(0, dtype=np.int64), repr=False)

    def fit(self, features: Floats, labels: Labels) -> Self:
        """Запомнить обучающую выборку."""
        if len(features) != len(labels):
            msg = f"признаков {len(features)}, меток {len(labels)}"
            raise ValueError(msg)
        if self.k < 1:
            msg = f"k должно быть не меньше 1, пришло {self.k}"
            raise ValueError(msg)

        self._features = features
        self._labels = labels
        logger.info("fit: запомнили %d примеров, k=%d", len(features), self.k)
        return self

    def predict(self, features: Floats) -> Labels:
        """Метка для каждой строки."""
        if len(self._features) == 0:
            msg = "модель не обучена: сначала fit()"
            raise RuntimeError(msg)

        neighbours = min(self.k, len(self._features))
        predictions = np.empty(len(features), dtype=np.int64)

        for row_index, row in enumerate(features):
            distances = squared_distances(self._features, row[None, :]).ravel()
            nearest = np.argsort(distances)[:neighbours]
            votes = np.bincount(self._labels[nearest])
            predictions[row_index] = int(votes.argmax())

        logger.info("predict: %d точек, соседей=%d", len(features), neighbours)
        return predictions
