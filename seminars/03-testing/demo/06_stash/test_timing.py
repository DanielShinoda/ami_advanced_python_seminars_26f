import time


def test_fast() -> None:
    assert True


def test_slow() -> None:
    time.sleep(0.05)
    assert True
