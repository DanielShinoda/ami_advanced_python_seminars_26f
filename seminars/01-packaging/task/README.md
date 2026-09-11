# Задача семинара 1 — опубликовать пакет в TestPyPI

**Цель.** Пройти путь пакета целиком: исходники → `pyproject.toml` →
сборка → колесо → индекс → установка на чужой машине.

**Что уже есть.** В `textstat_template/` лежит **рабочий код**: модуль
`textstat_seminar` (статистика текста), CLI, файлы стоп-слов, тесты.
Код трогать не нужно.

**Что сделать.** Закрыть 6 TODO в `pyproject.toml`, собрать пакет и
опубликовать на **TestPyPI**.

---

## 0. До семинара

TestPyPI — отдельный сервис со своей базой пользователей, аккаунт с
pypi.org там не работает.

1. Регистрация: <https://test.pypi.org/account/register/>
2. Подтвердить email.
3. Включить 2FA — без неё загрузка не работает.
4. Создать API-токен: Account settings → API tokens → Add API token,
   scope «Entire account».
5. Сохранить токен **целиком**, с префиксом `pypi-`. Показывают один раз.

Токен — это пароль. В git он попасть не должен.

## 1. Имя пакета

`textstat` на TestPyPI давно занят, поэтому у каждого своё имя:

```
textstat-seminar-<твой-github-ник>
```

Нижний регистр. Например `textstat-seminar-danielshinoda`.

Имя **импорта** при этом у всех одно — `textstat_seminar`, менять его не
надо. Расхождение — норма: ставишь `pillow`, импортируешь `PIL`.

## 2. Шесть TODO

Открой `textstat_template/pyproject.toml`. Скучные поля (автор, лицензия,
классификаторы, ссылки) уже заполнены — посмотри, как они выглядят, и
иди к TODO.

| # | Что сделать |
|---|---|
| 1 | выбрать build-backend, заполнить `[build-system]` |
| 2 | `name` — имя дистрибутива со своим ником |
| 3 | `version` |
| 4 | `description` и `readme` |
| 5 | `[project.scripts]` — чтобы появилась команда `textstat` |
| 6 | включить файлы стоп-слов в колесо |

**TODO 5 и 6 ломаются молча.** Сборка пройдёт, пакет опубликуется — а у
пользователя не будет команды или упадёт `FileNotFoundError`. Поэтому:

## 3. Собери и посмотри, что получилось

Из папки `textstat_template/`:

```bash
uv build
unzip -l dist/*.whl
```

В колесе должны быть:

- `textstat_seminar/core.py`, `cli.py`, `__init__.py`
- `textstat_seminar/data/stopwords_ru.txt` и `stopwords_en.txt` ← **TODO 6**
- `*.dist-info/entry_points.txt` ← **TODO 5**
- `*.dist-info/METADATA`

Метаданные глазами:

```bash
unzip -p dist/*.whl '*/METADATA' | head -20
```

Пустой `Summary:` — TODO 4 не закрыт.

## 4. Проверь локально

```bash
uv venv
uv pip install -e . pytest
uv run pytest                  # 15 тестов, все зелёные
```

Тесты не запустятся, пока пакет не установлен, — так и задумано.
Исходники лежат в `src/`, и Python их не найдёт без установки.

## 5. Опубликуй

```bash
export UV_PUBLISH_URL=https://test.pypi.org/legacy/
export UV_PUBLISH_TOKEN=pypi-XXXX
uv publish
```

Через переменные окружения, чтобы токен не осел в истории shell.

Пакет появится на `https://test.pypi.org/project/textstat-seminar-<ник>/`.

## 6. Проверь установку с нуля

Самое важное. Чистое окружение, никакого локального кода:

```bash
cd /tmp && uv venv proba && cd proba
uv pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  textstat-seminar-<ник>

uv run textstat --version
echo "Кот сидел на окне. Кот смотрел на птиц." | uv run textstat
```

## 7. Автопроверка

Из корня репозитория семинаров:

```bash
make check-pub USERNAME=<твой-ник>
```

Скрипт сходит в TestPyPI, проверит метаданные, поставит пакет во
временное окружение и прогонит smoke-тест. Вывод — чек-лист с ✓ и ✗.

## Сдача

Пришли семинаристу:

1. Ссылку на страницу пакета на TestPyPI.
2. Вывод `make check-pub USERNAME=<ник>` — все галочки зелёные.

## Грабли

**Версию нельзя перезалить.** `400 File already exists`. Даже если
удалить релиз через сайт — имя файла занято навсегда. Поднимай версию
(`0.1.1`) и заливай заново. Поэтому сначала `unzip -l`, потом `publish`.

**Собралось, хотя `[build-system]` пустой.** Так и есть: сработал
исторический fallback на setuptools. Но в колесе не будет ни точки
входа, ни стоп-слов. «Собралось» — не критерий.

**Пакет поставился, а `textstat` не запускается.** TODO 5.

**`FileNotFoundError` на стоп-словах после установки.** TODO 6. Локально
работало, потому что исходники лежали рядом.

**403 при загрузке.** Не подтверждён email, не включён 2FA, или токен
скопирован без префикса `pypi-`.

**Залил на pypi.org вместо test.pypi.org.** Забыл `UV_PUBLISH_URL`.
Удалить нельзя, можно только yank.

## Бонус

- Сделать версию динамической (TODO 3, второй вариант) и убедиться, что
  правка `__version__` меняет имя колеса.
- Собрать тот же код вторым backend'ом и сравнить содержимое колёс.
- Настроить публикацию из GitHub Actions через trusted publishing —
  без токена вообще. Как это работает — в `extra.ipynb`.
