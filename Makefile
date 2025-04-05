install_hooks:
	uv run pre-commit install

ruff:
	uv run ruff check . --fix
	uv run ruff format .

mypy:
	uv run mypy .

test:
	uv run pytest
