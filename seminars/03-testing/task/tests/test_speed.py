"""Подопытные тесты: на них видно, работает ли плагин.

Запускать из корня репозитория:

    uv run pytest seminars/03-testing/task/tests/ -q

Ожидание при готовом плагине: 2 прошло, 1 упал (test_prediction_is_instant
падает по замыслу — knn брутфорсом так быстро не умеет).
"""

import numpy as np
import pytest

from minipipe import KNN


@pytest.fixture(scope="module")
def trained():
    generator = np.random.default_rng(0)
    features = generator.normal(0, 1, (3000, 8))
    labels = (generator.random(3000) > 0.5).astype(np.int64)
    return KNN(k=5).fit(features, labels), generator.normal(0, 1, (800, 8))


@pytest.mark.max_duration(5.0)
def test_prediction_fits_in_five_seconds(trained):
    model, queries = trained
    assert len(model.predict(queries)) == len(queries)


@pytest.mark.max_duration(0.001)
def test_prediction_is_instant(trained):
    """Упадёт, и это правильно: лимит миллисекунда, а knn идёт дольше."""
    model, queries = trained
    model.predict(queries)


def test_without_marker(trained):
    """Маркера нет — плагин не должен вмешиваться."""
    model, queries = trained
    assert len(model.predict(queries)) == len(queries)
