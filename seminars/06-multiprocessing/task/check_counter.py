#!/usr/bin/env python3
"""Проверка общего счётчика между процессами.

Гоняет заготовку сценариями с растущим числом инкрементов: без lock
гонка (read-modify-write двумя процессами) почти гарантированно съест
часть инкрементов, и итог будет меньше workers * times.

    make check-counter
"""

from dataclasses import dataclass
import importlib.util
import multiprocessing as mp
from pathlib import Path
import sys
from typing import Protocol, cast

TASK_DIR = Path(__file__).resolve().parent
SOLUTION = TASK_DIR / "shared_counter.py"

JOIN_TIMEOUT_SEC = 30.0


class CounterLike(Protocol):
    """Контракт, который верификатор требует от модуля."""

    def _bump(self, counter: object, lock: object, times: int) -> None: ...

    def count_parallel(self, workers: int, times: int) -> int: ...


@dataclass
class Check:
    title: str
    ok: bool
    detail: str = ""

    def render(self) -> str:
        mark = "\033[32m✓\033[0m" if self.ok else "\033[31m✗\033[0m"
        tail = f"  — {self.detail}" if self.detail else ""
        return f"  {mark} {self.title}{tail}"


def load_module() -> CounterLike:
    """Импортировать модуль заготовки (без установки пакета)."""
    spec = importlib.util.spec_from_file_location("student_shared_counter", SOLUTION)
    if spec is None or spec.loader is None:
        sys.exit(f"не могу импортировать {SOLUTION}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast("CounterLike", module)


def check_fair_play(code: str) -> list[Check]:
    """Решение должно делать общий счётчик, а не сумму локальных."""
    return [
        Check("используется fork-контекст", "get_context" in code),
        Check("инкременты под lock", "Lock" in code),
        Check("решение не обходит условие задачи", "_bump" in code and "counter" in code),
        Check(
            "все TODO закрыты",
            "NotImplementedError" not in code,
            "остались заглушки" if "NotImplementedError" in code else "",
        ),
    ]


def check_bump(module: CounterLike) -> Check:
    """_bump должен двигать ОБЩИЙ counter — не вернуть готовое число."""
    start, bump_times = 100, 5000
    ctx = mp.get_context("fork")
    counter = ctx.Value("i", start)
    lock = ctx.Lock()
    proc = ctx.Process(target=module._bump, args=(counter, lock, bump_times), daemon=True)
    proc.start()
    proc.join(timeout=JOIN_TIMEOUT_SEC)
    if proc.is_alive():
        proc.terminate()
        return Check("_bump двигает общий counter", False, "воркер завис")
    expected = start + bump_times
    return Check(
        "_bump двигает общий counter",
        counter.value == expected,
        f"получено {counter.value}, ожидалось {expected}" if counter.value != expected else "",
    )


def run_scenario(
    module: CounterLike, title: str, workers: int, times: int, repeat: int
) -> list[Check]:
    expected = workers * times
    checks: list[Check] = []
    for attempt in range(1, repeat + 1):
        try:
            got = module.count_parallel(workers=workers, times=times)
        except NotImplementedError:
            return [Check(f"{title}: заготовка не доделана", False, "NotImplementedError")]
        except Exception as exc:  # любой сбой решения — это провал прогона
            return [Check(f"{title}: прогон упал", False, f"{type(exc).__name__}: {exc}")]
        checks.append(
            Check(
                f"{title} (попытка {attempt}): итог {expected}",
                got == expected,
                f"получено {got}" if got != expected else "",
            )
        )
    return checks


def main() -> int:
    if not SOLUTION.exists():
        sys.exit(f"не нахожу {SOLUTION}")

    print("\nПроверяю \033[1mshared_counter.py\033[0m\n")
    code = SOLUTION.read_text(encoding="utf-8")
    checks = check_fair_play(code)

    print("  гоняю инкременты…\n")
    module = load_module()
    checks.append(check_bump(module))
    checks += run_scenario(module, "сценарий 1", workers=4, times=20_000, repeat=2)
    checks += run_scenario(module, "сценарий 2", workers=8, times=10_000, repeat=1)
    checks += run_scenario(module, "сценарий 3", workers=1, times=5, repeat=1)

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
