"""Считает средние по датчикам. Три записи битые, скрипт падает на первой.

Позиции битых записей выбираются заново на каждый запуск.
"""

import secrets

TOTAL = 20_000
BROKEN = 3


def read_value(record: dict[str, object]) -> float:
    """Достаёт значение. На битой записи падает."""
    return float(record["value"])  # type: ignore[arg-type]


def make_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = [
        {"index": i, "sensor": f"s-{i:05d}", "value": 1.0} for i in range(TOTAL)
    ]
    for _ in range(BROKEN):
        records[secrets.randbelow(TOTAL)]["value"] = None
    return records


def main() -> None:
    records = make_records()
    total = sum(read_value(record) for record in records)
    print("сумма:", total)


if __name__ == "__main__":
    main()
