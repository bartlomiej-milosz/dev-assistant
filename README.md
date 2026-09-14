# Dev Assistant

A local Python project exploring a question developers face when joining a codebase: *where does this repository implement a particular behavior?* The intended CLI retrieves passages from one Git repository and uses a local Ollama model to answer in English, with a citation to a specific file and commit.

## Current state

The foundation includes an installable CLI with help and version output, a locked development environment, a Docker build, and a notebook with two source-checked evaluation cases. The indexing and question-answering commands are planned. Retrieval results will be published in the notebook after the experiment.

## Run the foundation

Install Git, Make and uv. From the repository root:

```sh
make setup
make init-config
make run
make verify
```

`make init-config` creates `sources.toml` once. Edit the Git URL and branch there to select a repository. The [example configuration](sources.example.toml) selects Order & Inventory System. The scaffold does not fetch the configured source yet.

With Docker and Compose available, run `make build smoke` to build the runtime image and print the installed CLI version. Compose mounts the configuration read-only and provides a named volume for the future index.

## Project layout

| Path | Purpose |
| --- | --- |
| [src/dev_assistant](src/dev_assistant/) | Installed Python package and CLI entry point |
| [tests](tests/) | Automated package checks |
| [docs/design.md](docs/design.md) | Intended indexing, retrieval and citation behavior |
| [notebooks/retrieval-evaluation.ipynb](notebooks/retrieval-evaluation.ipynb) | Public experiment and demonstration |
| [notebooks/data](notebooks/data/) | Versioned questions and expected evidence |

## Open the experiment

Run `make notebooks`, open the notebook in VS Code with the Python and Jupyter extensions, and select the project's `.venv` kernel. Run all cells to inspect the starting questions and links to their reference passages. The notebook runs from either the repository root or the notebook directory.
