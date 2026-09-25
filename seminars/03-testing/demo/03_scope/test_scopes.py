"""Четыре области жизни фикстуры на четырёх тестах."""

import pytest


@pytest.fixture(scope="session", autouse=True)
def per_session() -> None:
    print("\n[session]  сработал")


@pytest.fixture(scope="module", autouse=True)
def per_module() -> None:
    print("[module]   сработал")


@pytest.fixture(scope="class", autouse=True)
def per_class() -> None:
    print("[class]    сработал")


@pytest.fixture(autouse=True)
def per_function() -> None:
    print("[function] сработал")


class TestParse:
    def test_title(self) -> None:
        assert True

    def test_body(self) -> None:
        assert True


class TestRender:
    def test_html(self) -> None:
        assert True

    def test_text(self) -> None:
        assert True
