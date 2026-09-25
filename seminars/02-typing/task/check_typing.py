#!/usr/bin/env python3
"""Проверка задачи семинара 2.

Что делает:

1. Гоняет `mypy --strict` по gradebook.py — ошибок быть не должно.
2. Смотрит, что проблему починили, а не заглушили (`type: ignore`, `cast`,
   лишний `Any`).
3. Прогоняет старые тесты — они должны остаться зелёными.
4. Проверяет поведение по контракту из README.

Запуск:

    uv run python seminars/02-typing/task/check_typing.py
"""

import ast
from collections.abc import Callable
from dataclasses import dataclass
import io
from pathlib import Path
import re
import subprocess
import sys

TASK_DIR = Path(__file__).resolve().parent
MODULE = TASK_DIR / "gradebook.py"
TESTS = TASK_DIR / "test_gradebook.py"

MYPY_TIMEOUT_SEC = 180
MAX_SHOWN_ERRORS = 3
PYTEST_TIMEOUT_SEC = 120

# Единственный Any, который разрешён: сырой JSON на входе parse_scores.
ALLOWED_ANY = "def parse_scores(payload: Any) -> list[float]:"
EXPECTED_SUMMARY = "Алиса — 9.00"


@dataclass
class Check:
    title: str
    ok: bool
    detail: str = ""

    def render(self) -> str:
        mark = "\033[32m✓\033[0m" if self.ok else "\033[31m✗\033[0m"
        tail = f"  — {self.detail}" if self.detail else ""
        return f"  {mark} {self.title}{tail}"


def check_mypy() -> list[Check]:
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-incremental", "--strict", str(MODULE)],
        capture_output=True,
        text=True,
        timeout=MYPY_TIMEOUT_SEC,
        cwd=TASK_DIR,
        check=False,
    )
    errors = [line for line in result.stdout.splitlines() if ": error:" in line]
    if not errors:
        return [Check("mypy --strict чистый", True, "0 ошибок")]

    shown = "; ".join(line.split(": error: ")[-1][:60] for line in errors[:MAX_SHOWN_ERRORS])
    more = f" (и ещё {len(errors) - MAX_SHOWN_ERRORS})" if len(errors) > MAX_SHOWN_ERRORS else ""
    detail = f"{len(errors)} ошибок: {shown}{more}"
    return [Check("mypy --strict чистый", False, detail[:150])]


def code_without_docstrings(source: str) -> str:
    """Убрать докстринги: в них про Any и type: ignore написано словами."""
    skip: set[int] = set()
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            skip.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return "\n".join(
        line for number, line in enumerate(source.splitlines(), 1) if number not in skip
    )


def check_not_silenced() -> list[Check]:
    """Баг должен быть починен, а не замазан."""
    source = code_without_docstrings(MODULE.read_text(encoding="utf-8"))
    checks: list[Check] = []

    ignores = re.findall(r"#\s*type:\s*ignore", source)
    checks.append(
        Check(
            "нет # type: ignore",
            not ignores,
            f"найдено {len(ignores)} шт. — это не починка, а глушилка" if ignores else "",
        )
    )

    casts = re.findall(r"\bcast\s*\(", source)
    checks.append(
        Check(
            "нет cast()",
            not casts,
            f"найдено {len(casts)} шт. — cast заставляет mypy поверить, но баг остаётся"
            if casts
            else "",
        )
    )

    any_lines = [
        line.strip()
        for line in source.splitlines()
        if re.search(r"\bAny\b", line) and not line.strip().startswith("#")
    ]
    # Отрезаем хвостовой комментарий: на разрешённой строке стоит noqa.
    extra = [
        line
        for line in any_lines
        if line.split("#")[0].strip() != ALLOWED_ANY and "import" not in line
    ]
    checks.append(
        Check(
            "Any не расползся",
            not extra,
            f"лишний Any: {extra[0][:60]}" if extra else "только на входе parse_scores",
        )
    )
    return checks


def check_tests() -> list[Check]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TESTS)],
        capture_output=True,
        text=True,
        timeout=PYTEST_TIMEOUT_SEC,
        cwd=TASK_DIR,
        check=False,
    )
    tail = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "нет вывода"
    return [Check("старые тесты зелёные", result.returncode == 0, tail[:80])]


def check_behaviour() -> list[Check]:
    """Каждый баг — отдельная проверка, чтобы было видно, что осталось."""
    sys.path.insert(0, str(TASK_DIR))
    for name in list(sys.modules):
        if name == "gradebook":
            del sys.modules[name]
    import gradebook as gb  # noqa: PLC0415

    checks: list[Check] = []
    students = [gb.Student("Алиса", "БПМИ251", [8, 10])]

    def probe(title: str, hint: str, action: Callable[[], tuple[bool, str]]) -> None:
        try:
            ok, detail = action()
        except Exception as exc:  # сломанный код падает как угодно — ловим всё
            ok, detail = False, f"{type(exc).__name__}: {exc} — {hint}"
        checks.append(Check(title, ok, detail))

    probe(
        "баг 1: average([]) не падает",
        "пустой список",
        lambda: (gb.average([]) == 0.0, f"вернулось {gb.average([])!r}, ждём 0.0"),
    )

    def missing_student() -> tuple[bool, str]:
        try:
            gb.score_of(students, "Никто")
        except KeyError:
            return True, "KeyError, как в контракте"
        except AttributeError:
            return False, "AttributeError на None — None не проверен"
        return False, "ничего не произошло, а ждём KeyError"

    probe("баг 2: score_of на отсутствующем", "find вернул None", missing_student)

    probe(
        "баг 3: summary_line собирает строку",
        "str + float",
        lambda: (
            gb.summary_line(students[0]) == EXPECTED_SUMMARY,
            f"{gb.summary_line(students[0])!r}, ждём {EXPECTED_SUMMARY!r}",
        ),
    )

    def auditors() -> tuple[bool, str]:
        buffer = io.StringIO()
        stdout, sys.stdout = sys.stdout, buffer
        try:
            gb.print_auditors([gb.Auditor("Виктор", "БПМИ255", [9], reason="в/с")])
        finally:
            sys.stdout = stdout
        printed = buffer.getvalue()
        return "Виктор" in printed, printed.strip().replace("\n", " | ")[:60]

    # Баг 4 — чисто статический: в рантайме Python на инвариантность list'а
    # не смотрит. Что он починен, говорит mypy; здесь лишь убеждаемся, что
    # печать вообще работает.
    probe("баг 4: печать вольнослушателей", "см. вывод mypy про list", auditors)

    def console() -> tuple[bool, str]:
        buffer = io.StringIO()
        stdout, sys.stdout = sys.stdout, buffer
        try:
            gb.publish_to_console("отчёт")
        finally:
            sys.stdout = stdout
        return buffer.getvalue().strip() == "отчёт", repr(buffer.getvalue().strip())

    probe("баг 5: publish_to_console работает", "ConsoleStorage не Storage", console)

    def scores() -> tuple[bool, str]:
        parsed = gb.parse_scores({"scores": ["8", "10"]})
        typed = all(type(value) is float for value in parsed)
        return parsed == [8.0, 10.0] and typed, f"{parsed!r} ({[type(v).__name__ for v in parsed]})"

    probe("баг 6: parse_scores отдаёт float", "Any пролез наружу", scores)
    return checks


def main() -> int:
    if not MODULE.exists():
        sys.exit(f"не нахожу {MODULE}")

    print("\nПроверяю \033[1mgradebook.py\033[0m\n")
    checks = check_mypy() + check_not_silenced() + check_tests() + check_behaviour()

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
