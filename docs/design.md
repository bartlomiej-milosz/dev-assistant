# How a question reaches its evidence

## Update

1. [corpus.py](../src/dev_assistant/corpus.py) reads the single HTTPS GitHub source and branch from TOML. A temporary bare Git repo fetches the branch or an explicit full SHA. Reading blobs from the resolved commit keeps uncommitted edits and mutable branch links out of citations.
2. Regular UTF-8 text blobs in supported formats, up to 256,000 bytes per file, are eligible. Hidden paths, common generated directories, symlinks and submodules are skipped. This is a file-selection policy, not a secret scanner.
3. A passage has a path, one-based inclusive line numbers and original text. Windows are 20 lines long with five lines of overlap. Markdown ATX headings outside fenced blocks introduce section boundaries. A long method may span several passages.
4. [model.py](../src/dev_assistant/model.py) embeds path and text in batches of 16 through Ollama's local HTTP API. A short-context embedding model can truncate input. A path helps distinguish files but can bias rankings. The service records the model tag, digest and dimension.
5. [storage.py](../src/dev_assistant/storage.py) submits bound SQL through SQLAlchemy Core with the pg8000 driver. A PostgreSQL transaction replaces all passages and the single snapshot row. A transaction-scoped advisory lock serializes publications, including initial schema creation. Readers see a complete committed version. Concurrent builders may repeat embedding work; the last successful publisher determines the active snapshot. The bounded corpus and vectors are buffered in memory before publication.

The CLI owns two tables in its dedicated database. The schema uses an unbounded-dimension pgvector column, while the application requires consistent dimensions across the snapshot. A full rebuild can therefore switch embedding models. PostgreSQL initializes the vector extension at first publication. The local Compose role owns this database; a shared deployment would provision the extension and roles independently.

## Ask

[service.py](../src/dev_assistant/service.py) retrieves at most three passages in a read-only use of a REPEATABLE READ transaction. The query observes the same snapshot metadata and rows even if an update commits between those reads. It releases the connection before generating an answer.

* **Text:** split camelCase and underscores while retaining the original text, index English lexemes in a tsvector, and OR the normalized query terms. Rank matching passages by ts_rank. This accepts partial matches and can also retrieve unrelated matches.
* **Vector:** embed the question using the digest recorded at indexing time, check dimensions and order by exact cosine distance with pgvector's `<=>`. Both queries break ties by path and first line. For this small corpus exact scans avoid approximate-index tuning.

The chat request contains a system instruction, the question and numbered source passages. Qwen returns JSON with one answer, one passage ID and one exact quotation. The application accepts only an integer ID belonging to this request and a nonempty substring from its body. It builds the link itself. Source zero, a fabricated quote or no passages lead to an insufficient-evidence answer. A malformed JSON response or transport failure is an operational error. These checks validate provenance. A genuine quote can still be irrelevant or support only part of an answer. The tool does not execute model output.

## Evidence and scope

The [notebook](../notebooks/retrieval-evaluation.ipynb) separates retrieval (path and any overlap with labelled lines), generation, abstention and an oracle-context control. Top-three location overlap does not measure factual accuracy. Negative controls cannot establish absence from every version of a project.

The application handles one repository with manual full refresh, English questions and one cited passage per answer. Cross-file architectural proofs, private multi-user access control, incremental indexing, approximate indexes and many-user serving are outside this implementation. Code and embeddings are stored in the local database. The demo uses public source and links to an immutable SHA.
