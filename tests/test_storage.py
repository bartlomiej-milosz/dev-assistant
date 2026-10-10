import os
from uuid import uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError

from dev_assistant.corpus import Passage
from dev_assistant.storage import Snapshot, current, database, replace, search

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1", reason="make test-db starts PostgreSQL"
)


@pytest.fixture
def engine():
    admin = database()
    schema = "test_" + uuid4().hex
    with admin.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text(f"CREATE SCHEMA {schema}"))
    isolated = database()

    @event.listens_for(isolated, "connect")
    def set_schema(raw, _):
        cursor = raw.cursor()
        cursor.execute(f"SET search_path TO {schema}, public")
        raw.commit()
        cursor.close()

    try:
        yield isolated
    finally:
        isolated.dispose()
        with admin.begin() as conn:
            conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        admin.dispose()


STATE = Snapshot("https://github.com/demo/repo", "a" * 40, "model@digest", 2)
A = Passage("A.sql", 1, 1, "reserve warehouse stock")
B = Passage("B.py", 1, 1, "normalize email")
VECS = [[1.0, 0.0], [0.0, 1.0]]


def test_real_cosine_keyword_and_replacement(engine):
    replace(engine, STATE, [A, B], VECS)
    with engine.connect() as conn:
        assert search(conn, "", VECS[1]) == [B, A]
        assert search(conn, "normalizing emails") == [B]
        assert search(conn, "elephant") == []
    replace(engine, STATE, [B], [VECS[1]])
    with engine.connect() as conn:
        assert search(conn, "", VECS[0]) == [B]
        assert current(conn) == STATE


def test_failed_write_keeps_exact_previous_state(engine):
    replace(engine, STATE, [A, B], VECS)
    other = Snapshot(STATE.url, "b" * 40, STATE.model, 2)
    with pytest.raises(IntegrityError):
        replace(engine, other, [B, B], VECS)
    with engine.connect() as conn:
        assert current(conn) == STATE
        assert search(conn, "", VECS[0]) == [A, B]


def test_reader_sees_one_commit_across_concurrent_publication(engine):
    replace(engine, STATE, [A], [VECS[0]])
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as reader:
        assert current(reader) == STATE
        other = Snapshot(STATE.url, "b" * 40, STATE.model, 2)
        replace(engine, other, [B], [VECS[1]])
        assert search(reader, "", VECS[0]) == [A]
    with engine.connect() as reader:
        assert current(reader) == other
        assert search(reader, "", VECS[0]) == [B]


def test_query_rejects_embedding_model_drift(engine, monkeypatch):
    from dev_assistant.model import Ollama
    from dev_assistant.service import retrieve

    replace(engine, STATE, [A], [VECS[0]])
    model = Ollama()
    try:
        monkeypatch.setattr(model, "identity", lambda: "new-digest")
        with pytest.raises(ValueError, match="differs"):
            retrieve(engine, model, "stock", "vector")
        assert retrieve(engine, model, "stock", "text")[1] == [A]
    finally:
        model.close()
