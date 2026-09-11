"""CLI-обёртка. Точка входа объявлена в pyproject.toml → [project.scripts].

Когда pip/uv ставит пакет, он читает `entry_points.txt` из .dist-info и
кладёт в bin/ маленький скрипт, который импортирует этот модуль и зовёт
`main()`. Посмотреть своими глазами: `cat .venv/bin/textstat`.
"""

import argparse
from pathlib import Path
import sys

from textstat_seminar import __version__
from textstat_seminar.core import Stats, analyze


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="textstat",
        description="Статистика текста: слова, предложения, самые частые слова.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="файл с текстом; без аргумента читает stdin",
    )
    parser.add_argument("-n", "--top", type=int, default=5, help="сколько частых слов показать")
    parser.add_argument(
        "-l",
        "--lang",
        choices=["ru", "en"],
        default=None,
        help="язык стоп-листа (по умолчанию определяется автоматически)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def format_stats(stats: Stats) -> str:
    rows = [
        ("символов", str(stats.chars)),
        ("без пробелов", str(stats.chars_no_spaces)),
        ("слов", str(stats.words)),
        ("уникальных слов", str(stats.unique_words)),
        ("предложений", str(stats.sentences)),
        ("средняя длина слова", f"{stats.avg_word_length}"),
        ("язык", stats.language),
    ]
    width = max(len(label) for label, _ in rows)
    lines = [f"{label:<{width}} : {value}" for label, value in rows]

    if stats.top_words:
        lines.append("")
        lines.append("частые слова:")
        lines.extend(f"  {count:>4}  {word}" for word, count in stats.top_words)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.path is None:
        text = sys.stdin.read()
    else:
        try:
            text = args.path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"не могу прочитать {args.path}: {exc}", file=sys.stderr)
            return 2

    if not text.strip():
        print("пустой текст — считать нечего", file=sys.stderr)
        return 1

    print(format_stats(analyze(text, top_n=args.top, language=args.lang)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
