# Local code/docs retrieval

The retrieval foundation indexes a configured directory and returns ranked excerpts
with relative filenames, line ranges, scores and citations. It uses local TF-IDF
cosine ranking over identifiers and words, including snake/camel-case splits.
There are no embeddings, vector database, external downloads or model calls.
`app/memory/vector_store.py` retains the existing placeholder module path; this
implementation is a lexical index rather than an embedding-backed vector store.

## Configure a corpus

Set RAG_ROOT in the backend environment to a curated directory you intend to make
searchable, then start the usual FastAPI service. No directory is indexed by
default, and clients cannot choose the root through a request.

```sh
RAG_ROOT=/absolute/path/to/curated/docs .venv/bin/python -m uvicorn app.main:app
```

Search the configured corpus:

```sh
curl -X POST http://127.0.0.1:8000/context/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"Docker timeout cleanup","top_k":5}'
```

The JSON response contains matches and index stats. Each match includes source,
start_line, end_line, text, truncated, score and a citation such as
`app/executor/runner.py:51-110`. Scores are ranking signals, not probabilities or
confidence. No matching terms yields an empty matches list. top_k is a strict
integer from 1 to 10; query length is bounded to 1–2000 characters. Missing or
unavailable corpus configuration returns HTTP 503 without revealing its host path.
The corpus is rebuilt per request, so file edits appear without a stale cache.

## File and resource policy

- Reads .py, .md, .rst, .txt, .js, .jsx, .ts and .tsx text files only.
- Skips hidden files/directories, symlinks, node_modules, workspace, venv, dist,
  build, outputs and Python caches. Invalid UTF-8 and NUL-containing files are skipped.
- Limits indexed files to 200, individual reads to 256 KiB, total accepted file bytes
  to 4 MiB, and chunks to 2000. Each excerpt is at most 12,000 characters and marks
  truncation. Oversized files are skipped. Stats expose whether a corpus budget was hit.
- Default chunks span 60 lines with 10 lines of overlap. Sorting/ranking tie-breaks
  are deterministic. Citations point to the source snapshot at request time.

This is NOT a secret scanner. Credentials embedded in ordinary code/docs can still
be returned. Only configure a corpus intended for callers of this backend; do not
point it at a home directory or credential store. There is no authentication or
per-user corpus isolation yet. Resource caps bound accepted corpus data, not total
filesystem traversal time, concurrent request load or memory overhead. File reads
are not hardened against an adversarial concurrent symlink/file swap.

## Tests and integration status

Run the backend unittest suite. The 13 new retrieval tests cover relevance,
source line overlap, excluded paths/symlinks, empty/no-match queries, deterministic
ties and top_k, binary/large files, corpus/chunk budgets, truncation, invalid chunk
settings, HTTP configuration failures, relative sources and refresh after file edits.
A repository smoke test found the requirements validator among five ranked hits.

Retrieval is not automatically added to planner/coder prompts yet, and no source
viewer/search control is delivered in React. There is no persistent index or
semantic paraphrase matching. Generated answers are not yet source-grounded by
this change. Next is bounded context injection with source attribution and tests;
retrieved text must be treated as untrusted reference content rather than instructions.
