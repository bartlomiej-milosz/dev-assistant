.PHONY: help setup check lint format typecheck test run

help:
	@printf '%s\n' \
	  'make help               Show all available commands' \
	  'make setup              Install locked runtime and development dependencies' \
	  'make check              Check lint, formatting and types (not tests)' \
	  'make lint               Check Python imports and lint rules with Ruff' \
	  'make format             Format Python files with Ruff' \
	  'make typecheck          Check Python types with ty' \
	  'make test               Run the default suite without PostgreSQL' \
	  'make run                Run the API locally with Uvicorn autoreload' \

setup:
	uv sync --locked

check: lint typecheck
	uv run --locked ruff format --check .

lint:
	uv run --locked ruff check .

format:
	uv run --locked ruff format .

typecheck:
	uv run --locked ty check

test:
	uv run --locked pytest

run:
	uv run dev-assistant
