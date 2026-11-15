# Saved runs

Completed normal and streaming API runs are archived in a local SQLite database
at data/runs.sqlite3. Override its location with MINI_DEVIN_HISTORY_DB. The database
and data directory are Git-ignored and excluded from retrieval ingestion.

GET /runs (or /api/runs) lists saved runs. GET /runs/{id} returns its prompt and
result, including generated files, attempts, execution/review and supplied context.
Both route families use the workspace-token guard when configured and no-store
cache headers. These are workspace-wide records, not per-user tenant accounts.

Load saved runs in the React UI, then select a record to restore it after a reload.
Up to 100 results are retained; oldest records are automatically pruned. A result
must serialize within 5 MiB to be archived. Prompts are capped at 20,000 characters
and list titles at 200 characters; full goal text remains in the result. SQLite
files have owner-only permissions. Records are plaintext, not encrypted; they may
contain private prompts, code or reference excerpts. Control host/backup access.

If saving fails, the API still returns the generated result with history_saved=false
and the UI explains it could not be saved. Failed requests before a complete result
and disconnected partial workflows are not archived. There is no arbitrary-file
read or database path parameter in the history API. Back up the configured SQLite
file while the app is stopped if longer retention is needed.
