"""Фикстура роняет прогон из teardown. Смотри, чем это кончится."""

import pytest


@pytest.fixture(autouse=True)
def _guard():
    yield
    raise AssertionError("фикстура решила уронить тест")


def test_looks_fine() -> None:
    assert True
