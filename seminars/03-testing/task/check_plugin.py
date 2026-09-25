#!/usr/bin/env python3
"""Проверка плагина pytest-maxduration.

Восемь пунктов: поведение маркера, устройство плагина и сборка в колесо.

    make check-plugin
"""

import ast
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TASK_DIR = Path(__file__).resolve().parent
PLUGIN = TASK_DIR / "pytest_maxduration.py"
PYPROJECT = TASK_DIR / "pyproject.toml"

PYTEST_TIMEOUT_SEC = 180
BUILD_TIMEOUT_SEC = 600

PROBE = """
import time

import pytest


@pytest.mark.max_duration(5.0)
def test_fast():
    assert True


@pytest.mark.max_duration(0.01)
def test_slow():
    time.sleep(0.05)


def test_no_marker():
    time.sleep(0.05)
"""

CONFTEST = 'pytest_plugins = ["pytest_maxduration"]\n'


@dataclass
class Check:
    title: str
    ok: bool
    detail: str = ""

    def render(self) -> str:
        mark = "\033[32m✓\033[0m" if self.ok else "\033[31m✗\033[0m"
        tail = f"  — {self.detail}" if self.detail else ""
        return f"  {mark} {self.title}{tail}"


def run(
    command: list[str], cwd: Path, timeout: int = PYTEST_TIMEOUT_SEC
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, capture_output=True, text=True, timeout=timeout, cwd=cwd, check=False
    )


def sandbox() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="maxduration-")


def prepare(root: Path, *, with_conftest: bool = True) -> None:
    shutil.copy(PLUGIN, root / PLUGIN.name)
    (root / "test_probe.py").write_text(PROBE.strip() + "\n", encoding="utf-8")
    if with_conftest:
        (root / "conftest.py").write_text(CONFTEST, encoding="utf-8")


def check_behaviour() -> list[Check]:
    """Пункты 1-4: что плагин делает с тестами."""
    with sandbox() as tmp:
        root = Path(tmp)
        prepare(root)

        markers = run([sys.executable, "-m", "pytest", "--markers"], root)
        result = run([sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider"], root)

    output = result.stdout
    registered = "max_duration" in markers.stdout

    def verdict(name: str) -> str:
        for line in output.splitlines():
            if f"::{name} " in line or f"::{name}[" in line:
                if "PASSED" in line:
                    return "PASSED"
                if "FAILED" in line:
                    return "FAILED"
        return "не найден"

    fast, slow, plain = verdict("test_fast"), verdict("test_slow"), verdict("test_no_marker")
    has_time = "c, лимит" in output or ("0.0" in output and slow == "FAILED")

    return [
        Check(
            "маркер зарегистрирован",
            registered,
            "виден в pytest --markers" if registered else "pytest --markers его не знает (TODO 2)",
        ),
        Check("быстрый тест с маркером проходит", fast == "PASSED", fast),
        Check("медленный тест падает", slow == "FAILED", slow),
        Check(
            "в сообщении видно фактическое время",
            slow == "FAILED" and has_time,
            "" if has_time else "в тексте ошибки нет ни времени, ни лимита",
        ),
        Check("тест без маркера не затронут", plain == "PASSED", plain),
    ]


def check_structure() -> list[Check]:
    """Пункты 5-6: Stash вместо атрибута, обёртка вокруг хука."""
    tree = ast.parse(PLUGIN.read_text(encoding="utf-8"))
    dump = ast.dump(tree)

    uses_stash = "StashKey" in dump
    assigns_attribute = any(
        isinstance(node, ast.Attribute)
        and isinstance(node.ctx, ast.Store)
        and node.attr.startswith("_")
        for node in ast.walk(tree)
    )
    uses_hookimpl = "hookimpl" in dump

    return [
        Check(
            "данные передаются через Stash",
            uses_stash and not assigns_attribute,
            "" if uses_stash and not assigns_attribute else "TODO 1: см. demo/06_stash",
        ),
        Check(
            "хук обёрнут через @pytest.hookimpl",
            uses_hookimpl,
            "" if uses_hookimpl else "TODO 4: см. demo/01_hooks",
        ),
    ]


def check_wheel() -> list[Check]:
    """Пункты 7-8: колесо с entry point и автоподхват в чистом окружении."""
    uv = shutil.which("uv")
    if uv is None:
        return [Check("колесо собирается", False, "uv не найден в PATH")]

    with sandbox() as tmp:
        root = Path(tmp)
        shutil.copy(PLUGIN, root / PLUGIN.name)
        shutil.copy(PYPROJECT, root / PYPROJECT.name)

        built = run([uv, "build", "--wheel"], root, BUILD_TIMEOUT_SEC)
        wheels = sorted((root / "dist").glob("*.whl")) if (root / "dist").exists() else []
        if built.returncode != 0 or not wheels:
            detail = built.stderr.strip().splitlines()[-1] if built.stderr.strip() else "нет .whl"
            return [
                Check("колесо собирается", False, detail[:150]),
                Check("pytest находит плагин сам", False, "колесо не собралось"),
            ]

        wheel = wheels[0]
        listing = run([sys.executable, "-m", "zipfile", "-l", str(wheel)], root)
        entry_points = run(
            [
                sys.executable,
                "-c",
                "import sys,zipfile;"
                "z=zipfile.ZipFile(sys.argv[1]);"
                "names=[n for n in z.namelist() if n.endswith('entry_points.txt')];"
                "print(z.read(names[0]).decode() if names else '')",
                str(wheel),
            ],
            root,
        )
        has_group = "[pytest11]" in entry_points.stdout
        packed = "pytest_maxduration.py" in listing.stdout

        declared = "py-modules" in PYPROJECT.read_text(encoding="utf-8")

        checks = [
            Check(
                "колесо собирается и модуль в нём есть",
                packed,
                wheel.name if packed else "pytest_maxduration.py не попал в колесо",
            ),
            Check(
                "модуль объявлен явно (py-modules)",
                declared,
                "setuptools угадал сам, полагаться на это не надо (TODO 6)" if not declared else "",
            ),
            Check(
                "в колесе entry point группы pytest11",
                has_group,
                entry_points.stdout.strip().replace("\n", " ")
                if has_group
                else "TODO 5: см. раздел 7 в ../README.md",
            ),
        ]
        if not (packed and has_group):
            checks.append(Check("pytest находит плагин сам", False, "сначала закрой TODO 5-6"))
            return checks

        venv = root / "clean"
        run([uv, "venv", str(venv)], root, BUILD_TIMEOUT_SEC)
        installed = run(
            [uv, "pip", "install", "--python", str(venv / "bin" / "python"), "pytest", str(wheel)],
            root,
            BUILD_TIMEOUT_SEC,
        )
        probe = root / "probe"
        probe.mkdir()
        (probe / "test_auto.py").write_text(PROBE.strip() + "\n", encoding="utf-8")

        auto = run(
            [str(venv / "bin" / "python"), "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            probe,
        )

    works = installed.returncode == 0 and "1 failed" in auto.stdout and "2 passed" in auto.stdout
    checks.append(
        Check(
            "pytest находит плагин сам, без conftest",
            works,
            "медленный тест упал в чистом окружении"
            if works
            else (auto.stdout.strip().splitlines()[-1] if auto.stdout.strip() else "нет вывода"),
        )
    )
    return checks


def main() -> int:
    if not PLUGIN.exists():
        sys.exit(f"не нахожу {PLUGIN}")

    print("\nПроверяю \033[1mpytest-maxduration\033[0m\n")
    checks = check_behaviour() + check_structure()
    print("  собираю колесо и ставлю в чистое окружение…\n")
    checks += check_wheel()

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
