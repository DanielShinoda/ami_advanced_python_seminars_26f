import pytest


@pytest.fixture
def prepared() -> str:
    print("    [фикстура] готовлю данные")
    return "ok"


def test_ok(prepared: str) -> None:
    print("    [тело] работаю")
    assert prepared == "ok"


def test_broken(prepared: str) -> None:
    print("    [тело] сейчас упаду")
    assert prepared == "не то"
