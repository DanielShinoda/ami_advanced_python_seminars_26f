#!/usr/bin/env python3
"""Проверка охоты за NaN.

Гоняет pdb с твоим commands.pdb несколько раз. Каждый прогон отравляет
другие строки, так что угадать нельзя — только найти.

    make check-hunt
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

TASK_DIR = Path(__file__).resolve().parent
SCRIPT = TASK_DIR / "nan_hunt.py"
COMMANDS = TASK_DIR / "commands.pdb"

RUNS = 4
RUN_TIMEOUT_SEC = 300

# Чего в commands.pdb быть не должно: это обход, а не отладка.
FORBIDDEN = {
    "NAN_HUNT_TRUTH": "чтение файла с ответом",
    "environ": "чтение переменных окружения",
    "_remember_truth": "вызов внутренней функции скрипта",
    "spoiled": "чтение готового списка отравленных",
    "import nan_hunt": "импорт модуля в обход прогона",
}


@dataclass
class Check:
    title: str
    ok: bool
    detail: str = ""

    def render(self) -> str:
        mark = "\033[32m✓\033[0m" if self.ok else "\033[31m✗\033[0m"
        tail = f"  — {self.detail}" if self.detail else ""
        return f"  {mark} {self.title}{tail}"


def check_fair_play() -> list[Check]:
    """Решение должно читать живые значения, а не ответ."""
    text = COMMANDS.read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))

    found = [why for token, why in FORBIDDEN.items() if token in code]
    has_commands = bool(re.search(r"^\s*b(reak)?\s", code, re.M))

    return [
        Check(
            "в commands.pdb есть команды",
            has_commands,
            "" if has_commands else "ни одной точки останова — файл пустой?",
        ),
        Check(
            "решение не обходит задачу",
            not found,
            f"найдено: {found[0]}" if found else "",
        ),
    ]


def one_run(truth_path: Path) -> tuple[list[tuple[int, str]], str]:
    """Один прогон pdb. Возвращает (истина, stdout)."""
    environment = dict(os.environ)
    environment["NAN_HUNT_TRUTH"] = str(truth_path)

    with COMMANDS.open("rb") as commands:
        result = subprocess.run(
            [sys.executable, "-m", "pdb", "-c", "continue", SCRIPT.name],
            stdin=commands,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SEC,
            cwd=TASK_DIR,
            env=environment,
            check=False,
        )

    truth: list[tuple[int, str]] = []
    if truth_path.exists():
        truth = [(int(i), str(s)) for i, s in json.loads(truth_path.read_text(encoding="utf-8"))]
    return truth, result.stdout


def check_runs() -> list[Check]:
    checks: list[Check] = []

    with tempfile.TemporaryDirectory(prefix="nan-hunt-") as tmp:
        truth_path = Path(tmp) / "truth.json"

        for attempt in range(1, RUNS + 1):
            truth_path.unlink(missing_ok=True)
            truth, output = one_run(truth_path)

            if not truth:
                checks.append(
                    Check(f"прогон {attempt}", False, "скрипт не дошёл до генерации данных")
                )
                continue

            # Сами значения не печатаем: это был бы ответ на задачу.
            missing = sum(
                1 for index, sensor in truth if str(index) not in output or sensor not in output
            )
            checks.append(
                Check(
                    f"прогон {attempt}: найдены все {len(truth)} строки",
                    missing == 0,
                    "" if not missing else f"не хватает {missing} из {len(truth)}",
                )
            )

    return checks


def main() -> int:
    for path in (SCRIPT, COMMANDS):
        if not path.exists():
            sys.exit(f"не нахожу {path}")

    print("\nПроверяю \033[1mcommands.pdb\033[0m\n")
    checks = check_fair_play()
    print(f"  гоняю pdb {RUNS} раза, каждый раз отравлены другие строки…\n")
    checks += check_runs()

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
