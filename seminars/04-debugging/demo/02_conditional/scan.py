"""Суммирует 50 000 показаний. Одно из них NaN, и сумма тоже NaN.

Скрипт не падает: NaN не поднимает исключений, он просто заражает ответ.
"""

import secrets

TOTAL = 50_000


def check(index: int, reading: float) -> float:
    """Пропускает показание дальше. Сюда и ставится точка останова."""
    return reading


def main() -> None:
    readings = [1.0] * TOTAL
    readings[secrets.randbelow(TOTAL)] = float("nan")

    total = 0.0
    for index, reading in enumerate(readings):
        total += check(index, reading)

    print("сумма:", total)


if __name__ == "__main__":
    main()
