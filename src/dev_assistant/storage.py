"""One transactional PostgreSQL snapshot, exact vector search and lexical ranking."""

import json
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import URL, Connection, Engine, create_engine, text

from dev_assistant.corpus import Passage

DDL = (
    "CREATE EXTENSION IF NOT EXISTS vector",
    """CREATE TABLE IF NOT EXISTS snapshot (
        singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
        url text NOT NULL, revision text NOT NULL, model text NOT NULL, dimensions int NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS passage (
        path text NOT NULL, start_line int NOT NULL, end_line int NOT NULL,
        body text NOT NULL, terms tsvector NOT NULL, embedding vector NOT NULL,
        PRIMARY KEY (path, start_line)
    )""",
)


def database(env_file: Path = Path(".env")) -> Engine:
    settings = {**dotenv_values(env_file), **os.environ}
    if not settings.get("DB_PASSWORD"):
        raise ValueError("Missing DB_PASSWORD. Run make init-env in the project root.")
    url = URL.create(
        "postgresql+pg8000",
        username="assistant",
        password=settings["DB_PASSWORD"],
        host=settings.get("DB_HOST") or "127.0.0.1",
        port=int(settings.get("DB_PORT") or "55438"),
        database="assistant",
    )
    return create_engine(url)


def lexical(value: str) -> str:
    # Preserve identifiers and add their component words for prose queries.
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value).replace("_", " ")
    return value + " " + words


@dataclass(frozen=True)
class Snapshot:
    url: str
    revision: str
    model: str
    dimensions: int


def replace(
    engine: Engine, state: Snapshot, passages: Sequence[Passage], vectors: list[list[float]]
) -> None:
    if not passages or len(passages) != len(vectors) or state.dimensions <= 0:
        raise ValueError("A complete, nonempty set of embeddings is required.")
    rows: list[dict[str, str | int]] = []
    for part, vector in zip(passages, vectors, strict=True):
        if len(vector) != state.dimensions or not any(vector):
            raise ValueError("Invalid embedding dimensions or zero vector.")
        rows.append(
            dict(
                path=part.path,
                start=part.start,
                end=part.end,
                body=part.body,
                terms=lexical(part.path + " " + part.body),
                vec=json.dumps(vector, allow_nan=False),
            )
        )
    with engine.begin() as conn:
        # Serialize publications, including first-time DDL. Readers see only committed snapshots.
        conn.execute(text("SELECT pg_advisory_xact_lock(639281437)"))
        for stmt in DDL:
            conn.execute(text(stmt))
        conn.execute(text("DELETE FROM passage"))
        conn.execute(text("DELETE FROM snapshot"))
        conn.execute(
            text("""INSERT INTO snapshot (url,revision,model,dimensions)
            VALUES (:url,:revision,:model,:dimensions)"""),
            vars(state),
        )
        conn.execute(
            text("""INSERT INTO passage (path,start_line,end_line,body,terms,embedding)
            VALUES (:path,:start,:end,:body,to_tsvector('english',:terms),CAST(:vec AS vector))"""),
            rows,
        )


def current(conn: Connection) -> Snapshot:
    if conn.scalar(text("SELECT to_regclass('snapshot')")) is None:
        raise ValueError("Empty index. Run dev-assistant update.")
    row = conn.execute(text("SELECT url, revision, model, dimensions FROM snapshot")).one_or_none()
    if row is None:
        raise ValueError("Empty index. Run dev-assistant update.")
    return Snapshot(*row)


def search(conn: Connection, question: str, vector: list[float] | None = None) -> list[Passage]:
    if vector is None:
        # OR across English lexemes. An AND query is too restrictive for full questions.
        stmt = """WITH query AS (
            SELECT to_tsquery('simple', string_agg(quote_literal(term), ' | ')) AS q
            FROM unnest(tsvector_to_array(to_tsvector('english', :question))) AS term
        ) SELECT path,start_line,end_line,body FROM passage,query WHERE terms @@ q
          ORDER BY ts_rank(terms,q) DESC,path,start_line LIMIT 3"""
        rows = conn.execute(text(stmt), {"question": lexical(question)})
    else:
        rows = conn.execute(
            text("""SELECT path,start_line,end_line,body FROM passage
            ORDER BY embedding <=> CAST(:vector AS vector),path,start_line LIMIT 3"""),
            {"vector": json.dumps(vector, allow_nan=False)},
        )
    return [Passage(*row) for row in rows]
