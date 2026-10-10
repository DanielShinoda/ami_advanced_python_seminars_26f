"""Базовые тесты TokenBucket.

Запуск из корня репо:  uv run pytest seminars/05-threads/task -q
До решения падают на NotImplementedError — это нормально.
"""

import threading
import time

from rate_limiter import TokenBucket


def test_burst_allows_burst_without_waiting() -> None:
    bucket = TokenBucket(rate=1000.0, burst=5)
    start = time.monotonic()
    for _ in range(5):
        bucket.acquire()
    assert time.monotonic() - start < 0.2


def test_empty_bucket_blocks_until_refill() -> None:
    bucket = TokenBucket(rate=50.0, burst=1)
    bucket.acquire()  # единственный токен ушёл
    start = time.monotonic()
    bucket.acquire()  # ждём ~1/50 с
    assert time.monotonic() - start >= 0.015


def test_refill_never_exceeds_burst() -> None:
    bucket = TokenBucket(rate=1000.0, burst=3)
    time.sleep(0.05)  # набежало бы 50 токенов — но вместимость 3
    for _ in range(3):
        bucket.acquire()
    start = time.monotonic()
    bucket.acquire()  # четвёртый ждёт refill
    assert time.monotonic() - start >= 0.0005


def test_consumers_dont_double_spend() -> None:
    bucket = TokenBucket(rate=10_000.0, burst=10)
    spent = 0
    spent_lock = threading.Lock()

    def spend() -> None:
        nonlocal spent
        bucket.acquire()
        with spent_lock:
            spent += 1

    threads = [threading.Thread(target=spend) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert spent == 10  # каждый acquire — ровно один токен, потерь нет
