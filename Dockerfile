FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.14-slim AS build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

FROM build AS checks
COPY tests ./tests
RUN uv sync --locked --no-editable \
    && uv run --locked --no-sync ruff format --check src tests \
    && uv run --locked --no-sync ruff check src tests \
    && uv run --locked --no-sync ty check src tests \
    && uv run --locked --no-sync pytest -q

FROM python:3.14-slim AS runtime
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
RUN mkdir -p /app/data && chown 10001:10001 /app/data
ENV PATH="/app/.venv/bin:${PATH}"
USER 10001:10001
ENTRYPOINT ["dev-assistant"]
CMD ["--help"]
