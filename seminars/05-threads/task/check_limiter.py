#!/usr/bin/env python3
"""Проверка token bucket на threading.Condition.

Гоняет заготовку стресс-прогонами:
  - инвариант бакета: в любом окне длины burst/rate съедено
    не больше burst + rate * окно токенов;
  - живучесть: все потоки завершаются, ни одного acquire не потеряно;
  - нижняя граница времени: быстрее, чем позволяет refill, нельзя.

    make check-limiter
"""

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
import threading
import time
from typing import Protocol, TypedDict, cast

TASK_DIR = Path(__file__).resolve().parent
SOLUTION = TASK_DIR / "rate_limiter.py"

RUN_TIMEOUT_SEC = 30.0
# Допуск на float-арифметику в refill: корректное решение укладывается
# в границу точно, лишние полтокена — уже следствие бага.
EPS_TOKENS = 0.5


class BucketLike(Protocol):
    """Контракт, который верификатор требует от TokenBucket."""

    def __init__(self, rate: float, burst: int) -> None: ...

    def acquire(self) -> None: ...


class StressResult(TypedDict):
    stamps: list[float]
    elapsed: float
    completed: int
    hung: int


@dataclass
class Check:
    title: str
    ok: bool
    detail: str = ""

    def render(self) -> str:
        mark = "\033[32m✓\033[0m" if self.ok else "\033[31m✗\033[0m"
        tail = f"  — {self.detail}" if self.detail else ""
        return f"  {mark} {self.title}{tail}"


def load_bucket_class() -> type[BucketLike] | None:
    """Импортировать TokenBucket из заготовки (без установки пакета)."""
    spec = importlib.util.spec_from_file_location("student_rate_limiter", SOLUTION)
    if spec is None or spec.loader is None:
        sys.exit(f"не могу импортировать {SOLUTION}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    klass = getattr(module, "TokenBucket", None)
    if klass is None:
        return None
    return cast("type[BucketLike]", klass)


def check_fair_play() -> list[Check]:
    """Решение должно ждать через Condition, а не спать и не отмазаться."""
    text = SOLUTION.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))

    forbidden = [
        ("sleep(", "ожидание через sleep вместо cond.wait"),
        ("asyncio", "asyncio здесь ни при чём"),
        ("threading.Semaphore", "по условию нужна Condition, не Semaphore"),
        ("from queue import", "по условию нужна Condition, не очередь"),
    ]
    found = [why for token, why in forbidden if token in code]

    return [
        Check("используется threading.Condition", "threading.Condition" in code),
        Check("инвариант проверяется в цикле", "while" in code),
        Check("решение не обходит условие задачи", not found, found[0] if found else ""),
        Check(
            "все TODO закрыты",
            "NotImplementedError" not in code,
            "остались заглушки" if "NotImplementedError" in code else "",
        ),
    ]


def stress(
    bucket_class: type[BucketLike], rate: float, burst: int, workers: int, per_worker: int
) -> StressResult:
    """Прогон: workers потоков делают по per_worker вызовов acquire.

    Зависших потоков не ждём вечно — живучесть проверяем по флагу hung.
    """
    bucket = bucket_class(rate=rate, burst=burst)
    stamps: list[float] = []
    stamps_lock = threading.Lock()
    finished = 0
    finished_lock = threading.Lock()

    def worker() -> None:
        nonlocal finished
        for _ in range(per_worker):
            bucket.acquire()
            with stamps_lock:
                stamps.append(time.monotonic())
        with finished_lock:
            finished += 1

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(workers)]
    start = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=RUN_TIMEOUT_SEC)
    elapsed = time.monotonic() - start

    return {
        "stamps": stamps,
        "elapsed": elapsed,
        "completed": finished * per_worker,
        "hung": sum(1 for t in threads if t.is_alive()),
    }


def invariant_break(stamps: list[float], rate: float, burst: int) -> int:
    """Число пар (i, j), где в окне [ts_i, ts_j] съедено слишком много.

    Если нарушение есть где-то, оно видно и на парах таймстампов —
    окно всегда можно сдвинуть к ближайшим событиям.
    """
    ts = sorted(stamps)
    window = burst / rate
    bad = 0
    for i in range(len(ts)):
        for j in range(i, len(ts)):
            span = ts[j] - ts[i]
            if span > window:
                break
            allowed = burst + rate * span + EPS_TOKENS
            if (j - i + 1) > allowed:
                bad += 1
    return bad


def run_scenario(
    bucket_class: type[BucketLike],
    title: str,
    rate: float,
    burst: int,
    workers: int,
    per_worker: int,
) -> list[Check]:
    total = workers * per_worker
    checks: list[Check] = []

    try:
        result = stress(bucket_class, rate, burst, workers, per_worker)
    except NotImplementedError:
        return [Check(f"{title}: заготовка не доделана", False, "NotImplementedError")]
    except Exception as exc:  # любой сбой решения — это провал прогона
        return [Check(f"{title}: прогон упал", False, f"{type(exc).__name__}: {exc}")]

    if result["hung"]:
        checks.append(
            Check(f"{title}: потоки завершились", False, f"{result['hung']} поток(а) зависли")
        )
        return checks
    checks.append(Check(f"{title}: потоки завершились", True))

    checks.append(
        Check(
            f"{title}: все {total} acquire доехали",
            result["completed"] == total,
            f"доехало {result['completed']} из {total}",
        )
    )

    bad = invariant_break(result["stamps"], rate, burst)
    checks.append(
        Check(
            f"{title}: инвариант бакета не нарушен",
            bad == 0,
            f"нарушений: {bad}" if bad else "",
        )
    )

    theoretical = (total - burst) / rate
    too_fast = result["elapsed"] < theoretical * 0.9
    checks.append(
        Check(
            f"{title}: не быстрее refill'а",
            not too_fast,
            f"{result['elapsed']:.2f} c при теории {theoretical:.2f} c" if too_fast else "",
        )
    )
    return checks


def main() -> int:
    if not SOLUTION.exists():
        sys.exit(f"не нахожу {SOLUTION}")

    print("\nПроверяю \033[1mrate_limiter.py\033[0m\n")
    checks = check_fair_play()

    bucket_class = load_bucket_class()
    if bucket_class is None:
        checks.append(Check("класс TokenBucket на месте", False, "не найден в модуле"))
    else:
        checks.append(Check("класс TokenBucket на месте", True))
        print("  гоняю стресс-прогоны…\n")
        checks += run_scenario(
            bucket_class, "прогон 1", rate=125.0, burst=25, workers=4, per_worker=60
        )
        checks += run_scenario(
            bucket_class, "прогон 2", rate=70.0, burst=7, workers=3, per_worker=20
        )

    print("Чек-лист:\n")
    for check in checks:
        print(check.render())

    failed = [check for check in checks if not check.ok]
    print()
    if failed:
        print(f"\033[31mНе пройдено: {len(failed)} из {len(checks)}\033[0m")
        return 1
    print(f"\033[32mВсё пройдено: {len(checks)} из {len(checks)}\033[0m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
