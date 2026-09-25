"""Тесты, передающие состояние друг другу. Ломаются под -n 2."""

USERS: list[str] = []


def test_add_user() -> None:
    USERS.append("alice")
    assert USERS == ["alice"]


def test_users_count() -> None:
    assert len(USERS) == 1
