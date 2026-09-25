"""Дальний от теста conftest."""

import pytest


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item):
    print("  [дальний conftest] до")
    result = yield
    print("  [дальний conftest] после")
    return result
