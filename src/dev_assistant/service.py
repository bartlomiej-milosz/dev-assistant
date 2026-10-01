"""Application operations shared by the CLI and the evaluation notebook."""

from sqlalchemy import Engine

from dev_assistant.corpus import Passage, Source, snapshot
from dev_assistant.model import Ollama
from dev_assistant.storage import Snapshot, current, replace, search


def update(
    engine: Engine, model: Ollama, source: Source, revision: str | None
) -> tuple[Snapshot, int]:
    commit, passages = snapshot(source, revision)
    if not passages:
        raise ValueError("No eligible text passages in this commit.")
    identity = model.identity()
    vectors = model.embed([p.path + "\n" + p.body for p in passages])
    if identity != model.identity():
        raise ValueError("Embedding model changed during update. Retry with a stable model.")
    state = Snapshot(source.url, commit, identity, len(vectors[0]))
    replace(engine, state, passages, vectors)
    return state, len(passages)


def retrieve(
    engine: Engine, model: Ollama, question: str, method: str
) -> tuple[Snapshot, list[Passage]]:
    if not question.strip():
        raise ValueError("Enter a nonempty question.")
    if method not in {"vector", "text"}:
        raise ValueError("Choose text or vector retrieval.")
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
        state = current(conn)
        vector = None
        if method == "vector":
            if model.identity() != state.model:
                raise ValueError("Embedding model differs from the snapshot. Rebuild with update.")
            vector = model.embed([question])[0]
            if len(vector) != state.dimensions:
                raise ValueError("Embedding dimensions differ. Rebuild with update.")
        return state, search(conn, question, vector)
