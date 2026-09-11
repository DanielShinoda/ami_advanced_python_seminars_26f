#!/usr/bin/env python3
"""Проверка публикации пакета семинара 1 на TestPyPI.

Что делает:

1. Спрашивает у TestPyPI метаданные пакета (JSON API).
2. Проверяет, что метаданные заполнены, а не остались пустыми.
3. Проверяет, что в релизе есть и wheel, и sdist.
4. Ставит пакет во временное чистое окружение (`uv venv`).
5. Прогоняет smoke-тест: импорт, стоп-слова, консольная команда.

Запуск:

    uv run python seminars/01-packaging/task/check_publication.py --username ivanov

Скрипт ничего не публикует и не требует токена — только читает.
"""

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any
import urllib.error
import urllib.request

TEST_PYPI_JSON = "https://test.pypi.org/pypi/{dist}/json"
TEST_PYPI_SIMPLE = "https://test.pypi.org/simple/"
PYPI_SIMPLE = "https://pypi.org/simple/"
IMPORT_NAME = "textstat_seminar"
SCRIPT_NAME = "textstat"
ENTRY_POINT = "textstat_seminar.cli:main"

HTTP_TIMEOUT_SEC = 30
INSTALL_TIMEOUT_SEC = 300
SMOKE_TIMEOUT_SEC = 60

SAMPLE_TEXT = "Кот сидел на окне. Кот смотрел на птиц! Птицы не смотрели на кота?"
EXPECTED_WORDS = 13
EXPECTED_SENTENCES = 3
MIN_STOPWORDS = 50
MIN_README_CHARS = 100  # README короче — скорее всего не подтянулся
MIN_CLASSIFIERS = 2
HTTP_NOT_FOUND = 404

# Скрипт, который выполняется внутри свежесозданного окружения.
# Каждый шаг обёрнут отдельно: если .txt не доехал в колесе, должна упасть
# проверка package data, а не "импорт не работает".
SMOKE_SCRIPT = f"""
import json
import traceback

result = {{}}

import {IMPORT_NAME}
result["version"] = {IMPORT_NAME}.__version__
result["location"] = {IMPORT_NAME}.__file__

from {IMPORT_NAME} import analyze, load_stopwords

try:
    result["stopwords_ru"] = len(load_stopwords("ru"))
    result["stopwords_en"] = len(load_stopwords("en"))
except Exception as exc:
    result["stopwords_error"] = f"{{type(exc).__name__}}: {{exc}}"

try:
    stats = analyze({SAMPLE_TEXT!r}, top_n=2)
    result["words"] = stats.words
    result["sentences"] = stats.sentences
    result["language"] = stats.language
    result["top_words"] = stats.top_words
except Exception as exc:
    result["analyze_error"] = f"{{type(exc).__name__}}: {{exc}}"

print(json.dumps(result, ensure_ascii=False))
"""


@dataclass
class Check:
    """Один пункт чек-листа."""

    title: str
    ok: bool
    detail: str = ""

    def render(self) -> str:
        mark = "\033[32m✓\033[0m" if self.ok else "\033[31m✗\033[0m"
        tail = f"  — {self.detail}" if self.detail else ""
        return f"  {mark} {self.title}{tail}"


def normalize(name: str) -> str:
    """Нормализация имени по PEP 503: то, что понимает индекс."""
    return re.sub(r"[-_.]+", "-", name).lower()


def fetch_metadata(dist: str) -> dict[str, Any]:
    """Забрать JSON с TestPyPI. Бросает SystemExit с понятным текстом."""
    url = TEST_PYPI_JSON.format(dist=normalize(dist))
    # S310: схема жёстко зашита в TEST_PYPI_JSON, из аргументов приходит
    # только имя пакета — file:// сюда не подставить.
    request = urllib.request.Request(url, headers={"User-Agent": "ami-seminar-checker/1.0"})  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SEC) as response:  # noqa: S310
            payload: dict[str, Any] = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == HTTP_NOT_FOUND:
            sys.exit(
                f"Пакет '{dist}' на TestPyPI не найден.\n"
                f"  Проверь: {TEST_PYPI_JSON.format(dist=normalize(dist))}\n"
                f"  Частые причины: опечатка в нике, публиковали на pypi.org "
                f"вместо test.pypi.org, загрузка не дошла."
            )
        sys.exit(f"TestPyPI ответил {exc.code} {exc.reason} на {url}")
    except urllib.error.URLError as exc:
        sys.exit(f"Не достучаться до TestPyPI: {exc.reason}")
    return payload


def check_metadata(info: dict[str, Any]) -> list[Check]:
    """Метаданные заполнены, а не остались дырами из шаблона."""
    checks: list[Check] = []

    summary = (info.get("summary") or "").strip()
    checks.append(
        Check(
            "description заполнен",
            bool(summary) and summary.upper() != "UNKNOWN",
            summary or "пусто — TODO 4 не закрыт (description)",
        )
    )

    description = (info.get("description") or "").strip()
    checks.append(
        Check(
            "readme подтянулся",
            len(description) > MIN_README_CHARS,
            f"{len(description)} символов" if description else "пусто — TODO 4 не закрыт (readme)",
        )
    )

    requires_python = (info.get("requires_python") or "").strip()
    checks.append(
        Check(
            "requires-python указан",
            bool(requires_python),
            requires_python or "пусто — а поле было заполнено в заготовке",
        )
    )

    author = (info.get("author") or info.get("author_email") or "").strip()
    checks.append(
        Check("автор указан", bool(author), author or "пусто — а поле было заполнено в заготовке")
    )

    license_value = (info.get("license_expression") or info.get("license") or "").strip()
    license_files: list[str] = info.get("license_files") or []
    license_detail = (
        license_value or ", ".join(license_files) or "пусто — а поле было заполнено в заготовке"
    )
    checks.append(Check("лицензия указана", bool(license_value or license_files), license_detail))

    classifiers: list[str] = info.get("classifiers") or []
    checks.append(
        Check(
            "classifiers проставлены",
            len(classifiers) >= MIN_CLASSIFIERS,
            f"{len(classifiers)} шт."
            if classifiers
            else "пусто — а поле было заполнено в заготовке",
        )
    )

    urls = info.get("project_urls") or {}
    checks.append(
        Check(
            "ссылки на проект есть",
            bool(urls),
            ", ".join(urls) if urls else "пусто — а поле было заполнено в заготовке",
        )
    )
    return checks


def check_artifacts(payload: dict[str, Any]) -> list[Check]:
    """В последнем релизе должны быть обе формы дистрибутива."""
    files: list[dict[str, Any]] = payload.get("urls") or []
    kinds = {item.get("packagetype") for item in files}
    names = [str(item.get("filename")) for item in files]

    return [
        Check(
            "wheel опубликован",
            "bdist_wheel" in kinds,
            ", ".join(n for n in names if n.endswith(".whl")) or "нет .whl",
        ),
        Check(
            "sdist опубликован",
            "sdist" in kinds,
            ", ".join(n for n in names if n.endswith(".tar.gz")) or "нет .tar.gz",
        ),
    ]


def run(
    command: list[str],
    *,
    timeout: int,
    stdin_text: str = "",
) -> subprocess.CompletedProcess[str]:
    """Запустить процесс, всегда закрыв ему stdin: иначе CLI зависнет на вводе."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        input=stdin_text,
        check=False,
    )


def install_into_temp_env(uv: str, dist: str, workdir: Path) -> tuple[Check, Path | None]:
    """Поставить пакет с TestPyPI в чистое окружение."""
    venv = workdir / "venv"
    created = run([uv, "venv", str(venv)], timeout=INSTALL_TIMEOUT_SEC)
    if created.returncode != 0:
        return Check("создано чистое окружение", False, created.stderr.strip()[:300]), None

    installed = run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(venv / "bin" / "python"),
            "--index-url",
            TEST_PYPI_SIMPLE,
            "--extra-index-url",
            PYPI_SIMPLE,
            dist,
        ],
        timeout=INSTALL_TIMEOUT_SEC,
    )
    if installed.returncode != 0:
        return Check("установка из TestPyPI", False, installed.stderr.strip()[:400]), None
    return Check("установка из TestPyPI", True, "в пустое окружение, без локального кода"), venv


def check_smoke(venv: Path) -> list[Check]:
    """Импорт, данные и консольная команда в установленном пакете."""
    checks: list[Check] = []
    python = venv / "bin" / "python"

    result = run([str(python), "-c", SMOKE_SCRIPT], timeout=SMOKE_TIMEOUT_SEC)
    if result.returncode != 0:
        tail = " | ".join(result.stderr.strip().splitlines()[-2:])
        checks.append(Check(f"import {IMPORT_NAME}", False, tail[:400]))
        return checks

    data: dict[str, Any] = json.loads(result.stdout.strip().splitlines()[-1])
    checks.append(Check(f"import {IMPORT_NAME}", True, f"версия {data['version']}"))

    if "stopwords_error" in data:
        checks.append(
            Check(
                "стоп-слова доехали в колесе",
                False,
                f"{data['stopwords_error']} — .txt не попал в wheel, TODO 6 не закрыт",
            )
        )
    else:
        stopwords_ok = (
            data["stopwords_ru"] >= MIN_STOPWORDS and data["stopwords_en"] >= MIN_STOPWORDS
        )
        checks.append(
            Check(
                "стоп-слова доехали в колесе",
                stopwords_ok,
                f"ru {data['stopwords_ru']}, en {data['stopwords_en']}",
            )
        )

    if "analyze_error" in data:
        checks.append(Check("analyze() считает правильно", False, data["analyze_error"]))
    else:
        counts_ok = data["words"] == EXPECTED_WORDS and data["sentences"] == EXPECTED_SENTENCES
        checks.append(
            Check(
                "analyze() считает правильно",
                counts_ok,
                f"слов {data['words']} (ждём {EXPECTED_WORDS}), "
                f"предложений {data['sentences']} (ждём {EXPECTED_SENTENCES})",
            )
        )

    script = venv / "bin" / SCRIPT_NAME
    if not script.exists():
        checks.append(Check(f"команда {SCRIPT_NAME}", False, f"нет {script} — TODO 5 не закрыт"))
        return checks

    version_run = run([str(script), "--version"], timeout=SMOKE_TIMEOUT_SEC)
    checks.append(
        Check(
            f"команда {SCRIPT_NAME} работает",
            version_run.returncode == 0,
            version_run.stdout.strip() or version_run.stderr.strip()[:200],
        )
    )

    cli_run = run([str(script), "--top", "2"], timeout=SMOKE_TIMEOUT_SEC, stdin_text=SAMPLE_TEXT)
    checks.append(
        Check(
            f"{SCRIPT_NAME} считает текст из stdin",
            cli_run.returncode == 0 and "слов" in cli_run.stdout,
            cli_run.stdout.splitlines()[2] if cli_run.returncode == 0 else cli_run.stderr[:200],
        )
    )
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--username", help="GitHub-ник: имя соберётся как textstat-seminar-<ник>")
    group.add_argument("--dist", help="полное имя дистрибутива, если оно нестандартное")
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="не ставить пакет, проверить только метаданные (быстро, без сети на install)",
    )
    args = parser.parse_args(argv)

    dist = args.dist or f"textstat-seminar-{args.username.strip().lower()}"
    print(f"\nПроверяю \033[1m{dist}\033[0m на TestPyPI\n")

    payload = fetch_metadata(dist)
    info: dict[str, Any] = payload.get("info") or {}
    version = info.get("version", "?")
    print(f"  найден: версия {version}")
    print(f"  страница: https://test.pypi.org/project/{normalize(dist)}/\n")

    checks: list[Check] = [Check("пакет опубликован на TestPyPI", True, f"версия {version}")]
    checks += check_metadata(info)
    checks += check_artifacts(payload)

    if not args.metadata_only:
        uv = shutil.which("uv")
        if uv is None:
            sys.exit("uv не найден в PATH — поставь uv или запусти с --metadata-only")

        print("  ставлю во временное окружение…\n")
        with tempfile.TemporaryDirectory(prefix="textstat-check-") as tmp:
            install_check, venv = install_into_temp_env(uv, dist, Path(tmp))
            checks.append(install_check)
            if venv is not None:
                checks += check_smoke(venv)

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
