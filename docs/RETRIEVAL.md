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

## Opt-in agent context

`POST /chat` and `POST /chat/stream` accept an optional strict boolean
`use_context`, default false. Example:

```json
{"prompt":"Build a Docker timeout helper", "use_context":true}
```

The React checkbox **Use project references** sends that flag. It starts unchecked
and explains that excerpts are sent to the selected model provider. Configuring
RAG_ROOT alone enables search but does not cause normal agent requests to send
corpus content to a model. Only opt in with a corpus appropriate for that provider.

Enabled runs retrieve once during planning, then reuse the same snapshot in
planning, initial coding, rewrites and review. Context uses at most three sources,
3000 text characters per source, and 12,000 serialized source-list characters.
The retrieval query uses the first 2000 prompt characters; the original user
request is preserved for the agents. References are JSON-encoded, explicitly
marked untrusted, and instructed not to override the user request/output schema.
This prompting is not a guarantee against prompt injection.

Configured context adds a `context` object to the normal result, or to the SSE
complete event's result. It has status ready, no_matches or unavailable and a
sources list containing the bounded text and citation metadata. Missing/unavailable
corpus configuration does not abort generation; that status is returned so clients
can see that no extra context was supplied. Disabled requests preserve the previous
five-field response shape and never call the retrieval index.

The React result view labels these **References supplied**, with expandable
citations/excerpts and explicit no-match/unavailable messages. This is input
attribution, not proof of actual model usage or generated-code correctness. There
is no requirement for models to generate output citations, no persistent index,
and no semantic paraphrase matching. Corpus content can itself contain errors or
sensitive data; existing file exclusions do not replace corpus curation.

Tests cover default-off behavior, excerpt limits, unavailable/no-match status,
prompt labeling/encoding across all four agents, one retrieval per request,
reference reuse through rewrites, sync/SSE result attribution, strict boolean
validation, and UI request opt-in/source display. No live model grounding quality,
Docker execution or deployed browser-to-model integration was verified.
