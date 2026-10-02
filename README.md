# Семинары — Продвинутый Python, АМИ ВШЭ (осень 2026)

Материалы семинаров: теория в ноутбуках + задачи. Семинарист —
[Даниэль Хайбулин](https://t.me/kiDaniel), группа 1.

Лекции, задачи с автопроверкой, дедлайны и баллы — в основном курсе через
[manytask](https://hsemanytask.org/ami-python-advanced). Этот репозиторий
их не заменяет: здесь то, что разбираем на семинаре руками.

## Семинары

| № | Тема | Материалы |
|---|---|---|
| 1 | Packaging: от файла на диске до `pip install` | [`seminars/01-packaging/`](seminars/01-packaging/) |
| 2 | Типы: что находит mypy и чего не видят тесты | [`seminars/02-typing/`](seminars/02-typing/) |
| 3 | Внутренности pytest: хуки, scope, свой плагин | [`seminars/03-testing/`](seminars/03-testing/) |
| 4 | Отладка: pdb из файла команд, охота за NaN | [`seminars/04-debugging/`](seminars/04-debugging/) |

С семинара 3 появляется сквозной проект [`minipipe/`](minipipe/) — он
живёт до конца курса: сначала мы его тестируем, потом отлаживаем,
ускоряем и профилируем.

## Справочные тетрадки

- [`notebooks/numpy.ipynb`](notebooks/numpy.ipynb) — массивы, оси,
  broadcasting, индексация, случайность. `minipipe` и всё, что мы будем
  ускорять, написано на numpy: если знаешь его шапочно, начни отсюда.
- [`notebooks/logging.ipynb`](notebooks/logging.ipynb) — `LogRecord`,
  фильтры, форматтеры, свой JSON-форматтер, `contextvars`.
- [`notebooks/introspection.ipynb`](notebooks/introspection.ipynb) —
  `inspect`, code objects, `dis`, рекурсивный обход `co_consts`.

## Установка

Всё через [uv](https://docs.astral.sh/uv/) — один инструмент на версии
Python, виртуальные окружения и зависимости.

```bash
# macOS
brew install uv

# Linux / WSL
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Дальше:

```bash
git clone https://github.com/DanielShinoda/ami_advanced_python_seminars_26f.git
cd ami_advanced_python_seminars_26f
uv sync          # создаст .venv с Python 3.14 и поставит всё нужное
```

Проверить:

```bash
uv run python --version    # Python 3.14.x
make help                  # список доступных команд
```

Нативный Windows не поддерживаем — только WSL 2 с Ubuntu.

## Команды

```
make sync        создать .venv и поставить зависимости
make nb          запустить JupyterLab
make lint        ruff check + проверка формата
make fmt         отформатировать и починить автофиксимое
make typecheck   mypy --strict
make test        pytest
make nb-run      прогнать все ноутбуки целиком (проверка, что не сгнили)
make nb-clean    снять outputs с ноутбуков перед коммитом
make check-pub   семинар 1: проверить публикацию студента
make check-typing  семинар 2: проверить починку gradebook.py
make check-plugin  семинар 3: проверить плагин pytest-maxduration
make check-hunt    семинар 4: проверить охоту за NaN
```

## Как устроены материалы

```
notebooks/                 справочные тетрадки (numpy)
seminars/
└── 01-packaging/
    ├── README.md          что нужно знать до семинара
    ├── seminar.ipynb      теория семинара (~50 минут)
    ├── extra.ipynb        то, что не влезло — читать необязательно
    └── task/
        ├── README.md      условие задачи
        ├── textstat_template/   заготовка, которую доделываешь
        └── check_publication.py автопроверка
```

Семинары 1-2 — ноутбуки (хранятся без выводов, запускай ячейки сверху
вниз). Семинар 3 и дальше — `README.md` с теорией плюс запускаемые
скрипты в `demo/`.

Семинар рассчитан на 80 минут: ~50 теории и ~25 на задачу. Всё, что
глубже, вынесено в `extra.ipynb` и на семинаре не разбирается.

## Конвенции

- Python 3.14, конфиги `ruff` и `mypy` совпадают с курсовыми — что зелено
  здесь, зелено и в CI курса.
- Русский язык в комментариях и условиях — норма, это учебный репозиторий.
- Ноутбуки перед коммитом прогоняются через `make nb-clean`.

## Нашёл ошибку

Открой issue или pull request. Опечатка в условии задачи — тоже повод.

## Лицензия

MIT, см. [LICENSE](LICENSE).
