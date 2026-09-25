# Задача — написать pytest-плагин

Маркер `@pytest.mark.max_duration(0.1)` должен ронять тесты, которые не
уложились в отведённое время.

```python
@pytest.mark.max_duration(0.5)
def test_fast(): ...  # проходит


@pytest.mark.max_duration(0.01)
def test_slow():  # падает, и в сообщении видно фактическое время
    time.sleep(0.05)


def test_plain(): ...  # маркера нет — плагин не вмешивается
```

## Что сделать

Шесть TODO: четыре в `pytest_maxduration.py`, два в `pyproject.toml`.

```bash
make check-plugin
```

Всё, что нужно, разбирали на семинаре: `demo/01_hooks`,
`demo/06_stash` и раздел 5 в [`../README.md`](../README.md).

## Посмотреть глазами

```bash
cd seminars/03-testing
uv run pytest task/tests/ -q
```

Из папки семинара, **не из папки задачи**: внутри `task/` свой
`pyproject.toml`, и `uv run` там поставит плагин как пакет. Тогда pytest
подхватит его дважды — по entry point и через `conftest.py` — и упадёт с
`ValueError: Plugin already registered`.

`tests/test_speed.py` гоняет `knn` из `minipipe`, он медленный. Ожидание
при готовом плагине: 2 прошло, 1 упал. Эти тесты не трогай.

## Главный пункт — восьмой

Пока плагин подключён через `pytest_plugins` в `conftest.py` и виден
только внутри этой папки. Закрыв TODO 5-6, ты собираешь его в колесо — и
pytest начинает находить его **сам** после установки.

Верификатор проверяет это буквально: собирает колесо, ставит в чистый
venv вместе с одним `pytest`, кладёт рядом тест с маркером и ждёт, что
тот упадёт. Без `conftest.py`, без `pytest_plugins`.

Именно так в твоё окружение попали `mocker` и `--cov`.

## Что не считается

Держать время в своём атрибуте на `item` вместо `Stash`. Работать будет,
проверку не пройдёт — почему, разбирали в `demo/06_stash`.

## Сдача

Вывод `make check-plugin`: 11 из 11.
