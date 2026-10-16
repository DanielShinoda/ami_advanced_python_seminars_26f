"""Базовые тесты общего счётчика.

Запуск из корня репо:  uv run pytest seminars/06-multiprocessing/task -q
До решения падают на NotImplementedError — это нормально.
"""

from shared_counter import count_parallel


def test_small_exact() -> None:
    assert count_parallel(workers=3, times=1000) == 3000


def test_single_process() -> None:
    assert count_parallel(workers=1, times=123) == 123


def test_repeated_runs_stay_exact() -> None:
    for _ in range(3):
        assert count_parallel(workers=4, times=5000) == 20_000
