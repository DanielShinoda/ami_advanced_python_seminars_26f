"""Обёртки вокруг трёх фаз прогона теста."""

import pytest


@pytest.hookimpl(wrapper=True)
def pytest_runtest_setup(item: pytest.Item):
    print(f"[setup]    готовим {item.name}")
    result = yield  # здесь отрабатывают фикстуры
    print(f"[setup]    {item.name} готов")
    return result


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item):
    print(f"[call]     до {item.name}")
    try:
        result = yield  # здесь выполняется тело теста
    except Exception as exc:
        print(f"[call]     {item.name} упал: {type(exc).__name__}")
        raise
    print(f"[call]     {item.name} прошёл")
    return result


@pytest.hookimpl(wrapper=True)
def pytest_runtest_teardown(item: pytest.Item):
    print(f"[teardown] убираем за {item.name}")
    return (yield)
