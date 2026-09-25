"""Session-фикстура: одна на прогон или одна на воркер?"""

import os
import uuid

import pytest


@pytest.fixture(scope="session")
def secret() -> str:
    value = uuid.uuid4().hex[:6]
    print(f"[session setup] secret={value} pid={os.getpid()}")
    return value


@pytest.mark.parametrize("i", range(4))
def test_uses_secret(i: int, secret: str, worker_id: str) -> None:
    print(f"test{i}: worker={worker_id} pid={os.getpid()} secret={secret}")
