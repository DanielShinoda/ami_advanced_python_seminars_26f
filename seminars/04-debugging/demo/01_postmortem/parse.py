"""Разбор показаний датчиков. Падает где-то в глубине."""

RAW = [
    "s-01:12.5",
    "s-02:13.0",
    "s-03:oops",
    "s-04:14.5",
]


def parse_value(chunk: str) -> float:
    sensor, raw = chunk.split(":")
    return float(raw)


def parse_all(chunks: list[str]) -> list[float]:
    return [parse_value(chunk) for chunk in chunks]


def main() -> None:
    values = parse_all(RAW)
    print("среднее:", sum(values) / len(values))


if __name__ == "__main__":
    main()
