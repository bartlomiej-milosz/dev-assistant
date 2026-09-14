# Repository Q&A design

This document describes the intended behavior. The [README](../README.md) records what can be run today.

## Index a snapshot

`dev-assistant update` reads one Git URL and branch from `sources.toml`, fetches the branch and records its commit. It reads committed text files for code, configuration and Markdown. Each passage carries the path, inclusive line range and snapshot identifier. Markdown headings and bounded windows of code lines are initial chunking choices to evaluate.

An update rebuilds the whole index. Build the replacement in a transaction or a temporary database and expose it only after success. Changing the configured URL replaces the old corpus on the next successful update. A failed index build leaves the previous snapshot usable. SQLite stores passages and vectors locally. For this corpus, cosine similarity can be calculated in Python.

## Answer a question

`dev-assistant ask "…"` searches the last complete snapshot and sends a small set of numbered passages and the English question to local Ollama. The application resolves a cited passage ID to the stored file, lines and commit. It quotes the original text. An unknown ID cannot produce a citation. If the retrieved passages offer insufficient evidence, the answer should say so. The application can validate a citation's location. Whether it supports the answer is assessed in the notebook.

## Evaluate retrieval and answers

Compare keyword search with embeddings on the same passages, questions and commit. Use the same embedding model for indexing and querying. Before running the comparison, label expected passages and set aside some questions. Report counts for answerable questions whose expected passage occurs in the first three hits. Score unsupported questions separately. Inspect quotations and answers manually, and record at least one mismatch with the query, retrieved text and interpretation. Include model identifiers, machine, snapshot and elapsed time with the results. See the [evaluation notebook](../notebooks/retrieval-evaluation.ipynb).
