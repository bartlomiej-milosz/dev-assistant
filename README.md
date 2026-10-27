# Dev Assistant

Ask an English question about one GitHub repository and get a short answer, a verbatim quotation and a link to the file at the indexed commit. Dev Assistant runs in Python with local Ollama models and PostgreSQL with pgvector. It reads committed source files and never runs the indexed project.

**Example:** *Which numeric user and group run the packaged backend?* For the Order & Inventory sample, the default search located the Dockerfile and Qwen returned `USER 10001:10001`. [Original evidence](https://github.com/bartlomiej-milosz/order-inventory-system/blob/2ed99aad2d60f1d6318d6aef5b1c02bfe51716eb/Dockerfile#L18)

## What the experiment found

The [executed Jupyter notebook](notebooks/retrieval-evaluation.ipynb) contains the ranked passages, generated answers, exact quotes, timings and a controlled retry with hand-selected evidence. It runs the same application code as the CLI.

| On the fixed 532-passage sample | PostgreSQL full-text search | Exact pgvector cosine search |
| --- | ---: | ---: |
| Development questions with labelled evidence in the top three | 2/4 | 2/4 |
| Held-out questions with labelled evidence in the top three | 6/6 | 4/6 |

Qwen abstained on both questions about unrecorded production data using vector retrieval. It also abstained on two answerable held-out questions. These are results on a small hand-labelled corpus. The default for this application is text search; use `--method vector` to compare.

## Run locally

Install Git, uv, Make, Docker with Compose, and Ollama. Start Ollama on the host. Run the following from the project root:

```sh
ollama pull all-minilm
ollama pull qwen3.5:9b
make setup db
uv run --locked dev-assistant update
uv run --locked dev-assistant ask "Which numeric user and group run the packaged backend?"
uv run --locked dev-assistant ask "How is an employee email normalized?" --method vector
```

`make db` generates a private local `.env`, copies [sources.example.toml](sources.example.toml) to `sources.toml` on first use and starts the database on loopback port 55438. The example selects the Order & Inventory repository. Edit its HTTPS GitHub URL and branch, then run `update` to replace the entire index. Index public repositories or repositories you have authorized Git to read in that environment. The indexed subset includes common source, SQL, Markdown and configuration files. Use trusted sources suitable for indexing.

Each successful update publishes one complete snapshot. An unsuccessful update preserves the previous one. `ask` uses the stored snapshot and the local model. Only fetching a new revision and the initial dependency/model downloads need network access outside the machine. If the model returns unsupported evidence, the CLI reports insufficient evidence. An unavailable database or Ollama service produces a command error.

## Run the CLI in Docker

```sh
make db build smoke
docker compose run --rm cli update
docker compose run --rm cli ask "Which numeric user and group run the packaged backend?"
```

The CLI shares the same database and connects to host Ollama through `host.docker.internal`. This path was verified on macOS with Docker Desktop. On a Linux host where Ollama listens only on loopback, use the native CLI with the Compose database. The desktop workflow needs no public model endpoint. Use `docker compose stop db` to stop the database and retain its named volume.

## Reproduce the notebook

```sh
make db notebooks
uv run --locked dev-assistant update --commit 2ed99aad2d60f1d6318d6aef5b1c02bfe51716eb
```

Select the project environment as the VS Code Jupyter kernel and run all cells. The notebook checks the repository and SHA before comparing results. The [question set](notebooks/data/questions.json) contains development, held-out and missing-evidence cases. The saved interpretation describes the published run. Model or hardware changes can produce different outputs.

## Verification and configuration

`make verify` runs Ruff formatting, lint, ty and pytest. `make test-db` includes integration tests in isolated schemas on real pgvector. Tests use deterministic vectors and stubbed model responses. The notebook exercises the actual models. GitHub Actions builds a checks image, starts a fresh database, runs integration tests and smoke-tests the packaged CLI.

Keep the generated database password while its volume exists. The native CLI reads `.env` in the project root. To change the host port, set `DB_PORT` there before starting Compose. `EMBED_MODEL` defaults to `all-minilm`, `CHAT_MODEL` to `qwen3.5:9b`. A changed embedding model or digest requires another `update`. The verified chat model accepts structured JSON with thinking disabled. See [design and limits](docs/design.md) for the implementation decisions.
