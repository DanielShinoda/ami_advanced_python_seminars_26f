"""Работа с ноутбуками семинаров: прогон целиком и снятие outputs.

Ноутбуки в репо хранятся **без** outputs — так они нормально диффаются
в git. Перед коммитом: ``make nb-clean``. Чтобы убедиться, что ноутбук
не сгнил (например, поменялась версия uv и ячейка со сборкой падает):
``make nb-run``.
"""

import argparse
from pathlib import Path
import sys

from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
import nbformat

# Ноутбук качает пакеты и собирает wheel — 60 секунд на ячейку мало.
CELL_TIMEOUT_SEC = 600


def find_notebooks(root: Path) -> list[Path]:
    """Все .ipynb под root, кроме чекпоинтов Jupyter."""
    return sorted(path for path in root.rglob("*.ipynb") if ".ipynb_checkpoints" not in path.parts)


def clean(path: Path) -> bool:
    """Снять outputs и execution_count. True, если файл изменился."""
    notebook = nbformat.read(path, as_version=4)
    changed = False

    for cell in notebook.cells:
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            cell["outputs"] = []
            changed = True
        if cell.get("execution_count") is not None:
            cell["execution_count"] = None
            changed = True

    # Счётчики в метаданных тоже держат мусор от прошлых запусков.
    if notebook.metadata.pop("widgets", None) is not None:
        changed = True

    if changed:
        nbformat.write(notebook, path)
    return changed


def run(path: Path) -> None:
    """Исполнить ноутбук целиком. Бросает CellExecutionError на падении."""
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=CELL_TIMEOUT_SEC,
        kernel_name="python3",
        # Ноутбук лежит рядом с демо-проектами и относительными путями —
        # исполняем из его директории, а не из корня репо.
        resources={"metadata": {"path": str(path.parent)}},
    )
    client.execute()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "clean", "check"])
    parser.add_argument("root", type=Path, help="директория с ноутбуками")
    args = parser.parse_args(argv)

    notebooks = find_notebooks(args.root)
    if not notebooks:
        print(f"ноутбуков не найдено под {args.root}")
        return 0

    failed = 0
    for path in notebooks:
        match args.command:
            case "clean":
                status = "очищен" if clean(path) else "уже чистый"
                print(f"  {path}: {status}")
            case "check":
                # Валидность формата без исполнения — дешёвая проверка.
                nbformat.validate(nbformat.read(path, as_version=4))
                print(f"  {path}: валиден")
            case "run":
                print(f"  {path}: прогон…", flush=True)
                try:
                    run(path)
                except CellExecutionError as exc:
                    failed += 1
                    print(f"  {path}: УПАЛ\n{exc}", file=sys.stderr)
                else:
                    print(f"  {path}: ок")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
