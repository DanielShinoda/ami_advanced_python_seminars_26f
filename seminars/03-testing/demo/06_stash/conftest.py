"""Stash: фикстура собирает, хук проверяет."""

import time

import pytest

# Ключ создаётся один раз на уровне модуля. Это объект, не строка.
STARTED_AT = pytest.StashKey[float]()


@pytest.fixture(autouse=True)
def _remember_start(request: pytest.FixtureRequest) -> None:
    request.node.stash[STARTED_AT] = time.perf_counter()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item):
    result = yield
    started = item.stash.get(STARTED_AT, None)
    if started is not None:
        print(f"  [хук] {item.name}: {time.perf_counter() - started:.4f} c")
    return result
