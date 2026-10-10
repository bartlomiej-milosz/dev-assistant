FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.14-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
FROM base AS build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

FROM build AS checks
ENV PATH="/app/.venv/bin:${PATH}"
COPY tests ./tests
RUN uv sync --locked --no-editable \
    && uv run --locked --no-sync ruff format --check src tests \
    && uv run --locked --no-sync ruff check src tests \
    && uv run --locked --no-sync ty check src tests \
    && uv run --locked --no-sync pytest -q

FROM base AS runtime
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
USER 10001:10001
ENTRYPOINT ["dev-assistant"]
CMD ["--help"]
