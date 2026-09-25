"""Ближний к тесту conftest."""

import pytest


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item):
    print("    [ближний conftest] до")
    result = yield
    print("    [ближний conftest] после")
    return result
