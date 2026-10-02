# Материалы семинаров — Продвинутый Python (АМИ ВШЭ, 26f)
#
# Всё через uv. Если uv нет: brew install uv (macOS) или
#   curl -LsSf https://astral.sh/uv/install.sh | sh (Linux/WSL)

.DEFAULT_GOAL := help
.PHONY: help sync lint fmt typecheck test nb nb-clean nb-run check-pub check-typing check-plugin check-hunt

help:  ## показать этот список
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

sync:  ## создать .venv и поставить зависимости
	uv sync

lint:  ## ruff check + проверка формата
	uv run ruff check .
	uv run ruff format --check .

fmt:  ## отформатировать и починить автофиксимое
	uv run ruff format .
	uv run ruff check --fix .

typecheck:  ## mypy --strict по коду материалов
	uv run mypy --strict seminars/ tools/

test:  ## pytest по материалам (тесты задач гоняются в venv задачи)
	uv run pytest

nb:  ## запустить JupyterLab
	uv run jupyter lab

nb-run:  ## прогнать все ноутбуки целиком (проверка, что не сгнили)
	uv run python tools/nb.py run seminars notebooks

nb-clean:  ## снять outputs со всех ноутбуков перед коммитом
	uv run python tools/nb.py clean seminars notebooks

check-pub:  ## семинар 1: проверить публикацию: make check-pub USERNAME=ivanov
	uv run python seminars/01-packaging/task/check_publication.py --username $(USERNAME)

check-typing:  ## семинар 2: проверить починку gradebook.py
	uv run python seminars/02-typing/task/check_typing.py

check-plugin:  ## семинар 3: проверить плагин pytest-maxduration
	uv run python seminars/03-testing/task/check_plugin.py

check-hunt:  ## семинар 4: проверить охоту за NaN
	uv run python seminars/04-debugging/task/check_hunt.py
