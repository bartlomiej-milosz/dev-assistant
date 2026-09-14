.DEFAULT_GOAL := help
.PHONY: help setup init-config check test verify run notebooks build smoke

help:
	@printf '%s\n' 'make setup        Install locked development dependencies' \
	  'make init-config  Create local sources.toml from the example' \
	  'make run          Show CLI help' \
	  'make verify       Run formatting, lint, types and tests' \
	  'make notebooks    Install the VS Code notebook kernel dependencies' \
	  'make build        Build the CLI container' \
	  'make smoke        Run the packaged CLI in Compose'

setup:
	uv sync --locked

init-config:
	@test -e sources.toml || cp -n sources.example.toml sources.toml

check:
	uv run --locked ruff format --check .
	uv run --locked ruff check .
	uv run --locked ty check src tests

test:
	uv run --locked pytest -q

verify: check test

run:
	uv run --locked dev-assistant --help

notebooks:
	uv sync --locked --group notebooks

build:
	docker compose build cli

smoke: init-config
	docker compose run --rm --no-deps cli --version
