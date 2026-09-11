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
```

## Как устроены материалы

```
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

Ноутбуки лежат **без выводов**: так диффы в git читаемые. Запускай
ячейки сам, сверху вниз.

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
