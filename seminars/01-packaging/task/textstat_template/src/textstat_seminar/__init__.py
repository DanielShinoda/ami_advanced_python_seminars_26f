"""textstat_seminar — маленькая статистика текста.

Обрати внимание: имя **импорта** (`textstat_seminar`) не совпадает с именем
**дистрибутива** (`textstat-seminar-<твой-ник>`), под которым пакет лежит
на TestPyPI. Так бывает сплошь и рядом: ставишь `pillow` — импортируешь
`PIL`, ставишь `scikit-learn` — импортируешь `sklearn`.
"""

from textstat_seminar.core import Stats, analyze, load_stopwords

# Единственный источник правды по версии. В pyproject.toml её не дублируем —
# подтягиваем через dynamic version (см. TODO в конфиге).
__version__ = "0.1.0"

__all__ = ["Stats", "__version__", "analyze", "load_stopwords"]
