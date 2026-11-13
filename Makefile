.DEFAULT_GOAL := help
.PHONY: test-db help setup init-config init-env db format format-check lint typecheck check test verify run notebooks build smoke

help:
	@printf '%s\n' 'make setup       Install locked Python dependencies' \
	  'make db          Initialize config and start local PostgreSQL' \
	  'make format      Apply Ruff formatting to source and tests' \
	  'make format-check Check Ruff formatting without editing files' \
	  'make lint        Check Python code and imports with Ruff' \
	  'make typecheck   Check Python types with ty' \
	  'make check       Run all static checks' \
	  'make test        Run unit tests' \
	  'make test-db     Run all tests with PostgreSQL' \
	  'make verify      Run static checks and unit tests' \
	  'make notebooks   Install the notebook kernel and runner' \
	  'make build smoke Build and verify the packaged command'

setup:
	uv sync --locked
init-config:
	@test -e sources.toml || cp -n sources.example.toml sources.toml
init-env:
	@if [ ! -e .env ]; then umask 077; set -C; secret=$$(openssl rand -hex 24) && printf 'DB_PASSWORD=%s\n' "$$secret" > .env; fi
db: init-env init-config
	docker compose up -d --wait db
format:
	uv run --locked ruff format src tests

format-check:
	uv run --locked ruff format --check src tests

lint:
	uv run --locked ruff check src tests

typecheck:
	uv run --locked ty check

check: format-check lint typecheck

test:
	uv run --locked pytest -q
test-db: db
	RUN_DB_TESTS=1 uv run --locked pytest -q

verify: check test
run:
	uv run --locked dev-assistant --help
notebooks:
	uv sync --locked --group notebooks
build: init-env
	docker compose build cli
smoke: db
	docker compose run --rm cli --version
