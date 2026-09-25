"""k-means: кластеризация методом ближайшего центра."""

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
class KMeans:
    """Разбиение на n_clusters групп. Инерция не растёт от шага к шагу."""

    n_clusters: int = 3
    max_steps: int = 50
    seed: int = 0

    centers_: Floats = field(default_factory=lambda: np.empty((0, 0)), repr=False)
    labels_: Labels = field(default_factory=lambda: np.empty(0, dtype=np.int64), repr=False)
    inertia_history_: list[float] = field(default_factory=list, repr=False)

    def fit(self, points: Floats) -> Self:
        """Найти центры. История инерции — в inertia_history_."""
        if self.n_clusters < 1:
            msg = f"кластеров должно быть хотя бы 1, пришло {self.n_clusters}"
            raise ValueError(msg)
        if len(points) < self.n_clusters:
            msg = f"точек {len(points)}, а кластеров просят {self.n_clusters}"
            raise ValueError(msg)

        generator = np.random.default_rng(self.seed)
        centers = points[generator.choice(len(points), self.n_clusters, replace=False)].copy()
        history: list[float] = []

        for step in range(self.max_steps):
            distances = squared_distances(points, centers)
            labels = distances.argmin(axis=1).astype(np.int64)
            history.append(float(distances.min(axis=1).sum()))

            moved = self._recompute(points, labels, centers)
            converged = np.allclose(moved, centers)
            centers = moved
            if converged:
                logger.info("kmeans: сошлось за %d шагов, инерция %.3f", step + 1, history[-1])
                break
        else:
            logger.warning("kmeans: не сошёлся за %d шагов", self.max_steps)

        final = squared_distances(points, centers)
        self.centers_ = centers
        self.labels_ = final.argmin(axis=1).astype(np.int64)
        self.inertia_history_ = history
        return self

    def _recompute(self, points: Floats, labels: Labels, centers: Floats) -> Floats:
        """Новые центры — средние своих точек. Пустой кластер остаётся на месте."""
        updated = np.empty_like(centers)
        for index in range(len(centers)):
            members = points[labels == index]
            if len(members) == 0:
                logger.warning("kmeans: кластер %d опустел, центр оставлен на месте", index)
                updated[index] = centers[index]
            else:
                updated[index] = members.mean(axis=0)
        return updated

    def predict(self, points: Floats) -> Labels:
        """Номер ближайшего центра для каждой точки."""
        if len(self.centers_) == 0:
            msg = "модель не обучена: сначала fit()"
            raise RuntimeError(msg)
        return squared_distances(points, self.centers_).argmin(axis=1).astype(np.int64)

    @property
    def inertia_(self) -> float:
        """Инерция после последнего шага."""
        if not self.inertia_history_:
            msg = "модель не обучена: сначала fit()"
            raise RuntimeError(msg)
        return self.inertia_history_[-1]
