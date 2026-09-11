"""Подсчёт статистики текста. Чистый Python, без зависимостей."""

from collections import Counter
from dataclasses import dataclass, field
from importlib.resources import files
import re
from typing import Literal

Language = Literal["ru", "en"]

# Слово — последовательность букв/цифр/подчёркиваний, дефис внутри слова
# оставляем ("из-за" — одно слово, а не два).
_WORD_RE = re.compile(r"\w+(?:-\w+)*", re.UNICODE)

# Конец предложения: точка/восклицательный/вопросительный, возможно подряд.
_SENTENCE_RE = re.compile(r"[.!?]+")

_CYRILLIC_RE = re.compile(r"[а-яёА-ЯЁ]")

# Доля кириллицы среди букв, выше которой считаем текст русским.
CYRILLIC_THRESHOLD = 0.3


@dataclass(frozen=True, slots=True)
class Stats:
    """Результат разбора текста."""

    chars: int
    chars_no_spaces: int
    words: int
    unique_words: int
    sentences: int
    avg_word_length: float
    language: Language
    top_words: list[tuple[str, int]] = field(default_factory=list)


def detect_language(text: str) -> Language:
    """Грубая эвристика: много кириллицы среди букв — считаем текст русским."""
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return "en"
    cyrillic = sum(1 for char in letters if _CYRILLIC_RE.match(char))
    return "ru" if cyrillic / len(letters) > CYRILLIC_THRESHOLD else "en"


def load_stopwords(language: Language) -> frozenset[str]:
    """Прочитать список стоп-слов, приложенный к пакету.

    Файл лежит **внутри** пакета (`textstat_seminar/data/`), а не рядом с
    исходниками в репозитории. Читаем через `importlib.resources`, а не
    через `Path(__file__).parent` — так работает и когда пакет установлен
    из wheel, и когда он внутри zip.

    Если после `pip install` здесь падает `FileNotFoundError` — значит
    .txt не попал в wheel. Это ровно та ошибка, ради которой package data
    и вынесена в задачу.
    """
    resource = files("textstat_seminar").joinpath("data", f"stopwords_{language}.txt")
    lines = resource.read_text(encoding="utf-8").splitlines()
    return frozenset(
        line.strip().lower() for line in lines if line.strip() and not line.startswith("#")
    )


def analyze(text: str, *, top_n: int = 5, language: Language | None = None) -> Stats:
    """Посчитать статистику текста.

    Args:
        text: исходный текст.
        top_n: сколько самых частых слов вернуть (стоп-слова исключаются).
        language: язык стоп-листа; None — определить автоматически.

    Returns:
        Заполненный `Stats`.

    Example:
        >>> stats = analyze("Кот сидел. Кот спал.", top_n=1)
        >>> stats.sentences
        2
        >>> stats.top_words
        [('кот', 2)]
    """
    if top_n < 0:
        msg = "top_n не может быть отрицательным"
        raise ValueError(msg)

    resolved = language if language is not None else detect_language(text)
    words = [match.group().lower() for match in _WORD_RE.finditer(text)]

    # Предложение считаем непустым куском текста между терминаторами.
    sentences = sum(1 for part in _SENTENCE_RE.split(text) if part.strip())

    stopwords = load_stopwords(resolved)
    meaningful = Counter(word for word in words if word not in stopwords)

    total_length = sum(len(word) for word in words)
    return Stats(
        chars=len(text),
        chars_no_spaces=sum(1 for char in text if not char.isspace()),
        words=len(words),
        unique_words=len(set(words)),
        sentences=sentences,
        avg_word_length=round(total_length / len(words), 2) if words else 0.0,
        language=resolved,
        top_words=meaningful.most_common(top_n),
    )
