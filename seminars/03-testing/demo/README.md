# Примеры к семинару 3

Шесть маленьких проектов. Обычные папки с `conftest.py` и тестами —
открывай, правь, запускай заново.

Команды — из папки семинара (`cd seminars/03-testing`):

| Папка | О чём | Команда |
|---|---|---|
| `01_hooks` | обёртки вокруг трёх фаз | `uv run pytest demo/01_hooks -q -s` |
| `02_nested_conftest` | кто внутри кого | `uv run pytest demo/02_nested_conftest -q -s` |
| `03_scope` | четыре области жизни фикстуры | `uv run pytest demo/03_scope -q -s` |
| `04_xdist` | scope под `-n 2` | см. раздел 4 в [`../README.md`](../README.md) |
| `05_fixture_cannot_fail` | почему исход проверяет хук | `uv run pytest demo/05_fixture_cannot_fail -q` |
| `06_stash` | фикстура собирает, хук проверяет | `uv run pytest demo/06_stash -q -s` |

Что смотреть в каждом выводе — в [`../README.md`](../README.md).

Часть примеров **падает намеренно**: `01_hooks` показывает, как упавший
тест приходит в обёртку, `04_xdist/test_shared.py` — как ломаются тесты с
общим состоянием, `05_fixture_cannot_fail` — что фикстура не умеет
ронять тест по-настоящему.
