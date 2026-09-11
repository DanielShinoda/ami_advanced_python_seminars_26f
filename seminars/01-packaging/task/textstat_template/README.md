# textstat

Маленькая утилита: считает статистику текста — слова, предложения, средняя
длина слова, самые частые слова без служебных.

Учебный пакет семинара «Продвинутый Python» (АМИ ВШЭ). Опубликован на
TestPyPI, в проде не применять.

## Установка

```bash
pip install --index-url https://test.pypi.org/simple/ textstat-seminar-<ник>
```

## Использование

Как библиотека:

```python
from textstat_seminar import analyze

stats = analyze("Кот сидел на окне. Кот смотрел на птиц!", top_n=3)
print(stats.words, stats.sentences)
print(stats.top_words)
```

Как команда:

```bash
textstat book.txt --top 10
cat book.txt | textstat --lang ru
```

Вывод:

```
символов            : 39
без пробелов        : 33
слов                : 8
уникальных слов     : 7
предложений         : 2
средняя длина слова : 3.75
язык                : ru

частые слова:
     2  кот
     1  сидел
     1  окне
```

## Лицензия

MIT.
