# Daily progress

## Day 1 — November 2, 2026

Inspected baseline commit 77e4472. Provider abstraction (Gemini/Groq), multi-file
projects and Docker execution already exist; the June checklist predates this code.

Implemented batch validation of generated file paths before any file content is
written. Rejects traversal, absolute and Windows-drive paths, backslashes, nulls,
empty names, duplicates, symlink escapes and file/directory conflicts. The executor
returns InvalidProjectPath without invoking Docker for invalid projects. Files are
written as UTF-8. This protects path handling; it is not a claim that runtime
container isolation has been fully audited.

Moved the live provider smoke call behind a manual entry point, so test discovery
no longer calls Groq or needs credentials. Added seven offline tests covering safe
nested paths, rejected paths, conflicts, symlinks, partial-batch behavior and the
executor failure response. Added the dated 15-day roadmap.

Validation:
- python3 -m unittest discover -s tests -v: 7 tests passed.
- python3 -m compileall -q app tests: passed.
- git diff --check: passed.
- Real Docker execution blocked: Docker service is not running (socket absent).
- Live provider, frontend, AWS and end-to-end checks not performed today.

Daily automation is active at 19:00 Asia/Kolkata through November 16. Next: Ollama
provider and provider contract tests. Infrastructure error handling and stronger
Docker isolation remain on the roadmap.

## Ollama milestone — November 4, 2026 (IST)

Completed the Day 2 deliverable on November 4 local time. This run arrived at
00:30 IST; it is not backdated to November 3. The saved checkout was read-only,
so development used a fresh upstream clone in a temporary writable folder.

Added an Ollama implementation of BaseLLM using the non-streaming generate API.
Model, server URL and timeout are configurable. Responses must contain completed,
nonempty text; transport errors, provider errors, malformed JSON and incomplete
responses fail explicitly. Provider selection now tolerates case and whitespace.
Added a credential-free environment example and provider setup/testing guide.

Validation:
- python3 -m unittest discover -s tests -v: all 15 tests passed (8 new provider
  tests plus the 7 existing workspace tests).
- Provider selection uses mocked constructors for Gemini/Groq/Ollama; Ollama
  checks cover payload, timeout, HTTP errors, connection errors, malformed and
  incomplete responses, and invalid configuration. No live API calls were made.
- python3 -m compileall -q app tests and git diff --check: passed.
- Live Ollama check not run: Ollama executable is unavailable in this environment.
- Docker check remains blocked: Docker service socket is absent.
- Live Gemini/Groq, model quality and end-to-end agent execution are not verified.

Implementation commit: 6dd1c53 (add Ollama provider with configurable generation
and offline tests). This documentation update is a separate focused commit.
Next: structured agent-output validation and predictable provider failures.

## Structured agent-output milestone — November 4, 2026 (IST)

Completed the Day 3 milestone following the user's request for today's work.
Synced the upstream Ollama commits into the saved project checkout first.

Replaced four separate parsing paths with one strict JSON/schema boundary for
planner, coder, rewrite and reviewer. Supports one surrounding Markdown fence
without deleting backticks within generated source. Rejects prose, multiple JSON
objects, invalid schema and coerced boolean strings. Provider initialization and
generation failures now have stable classification; /chat returns HTTP 502 with
only the error kind and agent stage, avoiding raw provider details in public errors.

Validation:
- All 21 offline unittest tests passed (6 new structured-response tests).
- Includes preserving code content, invalid-output classification, strict review
  booleans, provider initialization/generation failures, direct route error mapping,
  and stopping before execution on an invalid planner response.
- Python compilation and git diff --check passed.
- FastAPI/Starlette emitted Python 3.14 deprecation warnings; tests still passed.
- Route verification invokes the handler directly, not a live HTTP server.
- No live provider calls, Docker execution or complete model-driven workflow tested.
  Existing Ollama installation and Docker service limitations remain unresolved.

Implementation commit: 93251a1. Documentation is a separate focused commit.
Next: Docker hardening, container cleanup and execution-environment failures.

## Docker hardening milestone — November 6, 2026 (IST)

Fresh upstream checkout started at e18013e; no uncommitted work was overwritten.
Implemented the Day 4 Docker milestone after its original November 5 target.
Day 5's multi-file/dependency checks remain pending. The project is behind its
original dated roadmap; November 16 remains a target, not verified completion.

Changes: shared Docker launcher, unique container names, bounded forced cleanup
on normal/failure/timeout paths, dropped capabilities, read-only root filesystem,
non-root identity, init process and scratch filesystem. No-dependency execution
and syntax validation disable networking. Dependency projects retain network
access for compatibility; install/runtime separation is still required. Filenames
are passed as arguments instead of interpolated shell source. Docker missing/start
failures become structured ExecutionEnvironment results rather than syntax errors.

Validation:
- All 30 offline unittest tests passed (9 new Docker/executor tests).
- New coverage: command isolation flags, noninteractive stdin, timeout cleanup,
  cleanup failure preserving original results, safe dependency entry arguments,
  validation network mode, path escape rejection, missing Docker and exit 125
  classification, and preservation of real SyntaxError classification.
- python3 -m compileall -q app tests and git diff --check passed.
- docker info failed: Docker service socket absent. No live container checks,
  dependency install, resource enforcement or full model-driven workflow verified.
- FastAPI/Starlette Python 3.14 deprecation warnings remain.

Implementation commit: 3ee3aa0. Execution guide and progress recorded separately.
Next: multi-file/dependency execution checks and separated dependency installation,
then LangChain/LangGraph. Live Docker validation needs a running Docker service.

## Dependency isolation increment — November 7, 2026 (IST)

Started from upstream 6e5676d in a fresh isolated checkout; no existing work changed.
Moved dependency installation into its own network-enabled container. Dependencies
transfer through a temporary directory mounted read-only in the network-disabled
runtime. Failed installation skips execution; temporary dependencies are removed
on context exit. The default install requests wheels only and disables compilation.
This does not complete the Day 5 milestone: live multi-file/dependency execution
checks remain pending, and the overall roadmap remains behind its original dates.

Validation:
- All 32 offline tests passed (new install-failure and read-only-mount checks,
  updated dependency-stage separation test; existing regressions retained).
- Python compilation and git diff --check passed.
- Docker service still unavailable: docker info reports missing socket. Actual
  package imports, network denial and container resource behavior are unverified.
- Existing FastAPI/Starlette Python 3.14 deprecation warnings remain.
- Install/runtime each retain a 30-second timeout. Packages requiring source builds
  may fail. Requirements directives/direct references remain unrestricted, and the
  temporary dependency directory has no quota. No complete sandbox claim is made.

Implementation commit: 2bd03e0. Documentation/progress is a separate commit.
Next: requirements validation and multi-file execution checks, then orchestration.

### November 7 follow-up 1: requirements validation

Added a restricted requirements parser before Docker installation. Accepts package
names, extras, version constraints and comments. Rejects local paths, URLs, editable
installs, pip options, nested files and environment markers. Comment-only files skip
installation; invalid files return a structured InvalidRequirements result.
All 36 offline tests pass; compilation and whitespace checks pass. This validates
syntax and source restrictions, not package trust or real wheel availability.

### November 7 follow-up 2: multi-file execution checks

Added five offline executor tests covering nested entries and all-file writes,
module-only validation, syntax failures stopping runtime, repeated-run workspace
isolation, and empty/non-Python projects. Fixed false success for projects with
no Python files: they now return UnsupportedProject. Nested entry discovery and
Python-file collection now use deterministic ordering.

All 41 offline tests passed; compilation and whitespace checks passed. Docker
calls are mocked in these checks: nested code imports and actual dependency
installation still require live Docker validation. Existing Python 3.14 library
deprecation warnings remain. These two follow-up commits advance the Day 5 code
milestone without claiming its live integration checks are complete.

## LangGraph orchestration milestone — November 8, 2026 (IST)

Started at upstream 18072d0, with a clean temporary checkout and no overwritten
work. Replaced the manager's loop with LangGraph shared-state nodes using
LangChain Core RunnableLambda. Retained provider adapters and API response fields.
The graph carries attempt history, caps total attempts, rewrites with review
feedback, and stops environment failures without another model review/rewrite.
A reviewer can no longer mark a failed execution as a successful attempt.

Dependency verification found FastAPI 0.104.1's AnyIO <4 requirement conflicting
with the new dependency set. Updated FastAPI to 0.162.2 and pinned LangGraph
1.2.20 / LangChain Core 1.7.6. Verified a clean install of all project requirements
plus HTTPX 0.28.1 (also provided transitively) in a separate environment.

Validation:
- All 54 offline tests passed in both the initial and clean environments (13 new
  graph/API tests). Real LangGraph execution with stubbed agents/executor.
- Covers bounded retries, feedback/history, isolated requests, environment failure
  short-circuit, rejecting false execution success, provider failure propagation,
  graph stage updates, custom attempt limit, actual in-process POST /chat success,
  HTTP 502 mapping, and HTTP 422 request validation.
- Clean-environment pip check: no broken requirements found.
- Python compilation and git diff --check passed.
- LangSmith emitted an asyncio deprecation warning under Python 3.14; clean tests
  passed. No live model requests, live Docker execution or deployed server checks.

Implementation commit: 6349379. Separate orchestration guide/progress commit follows.
This delivers graph orchestration and LangChain Core runnable composition, not
LangChain chat-model adapters. State remains request-local; checkpoint/resume,
HTTP streaming, cancellation and durable history are still pending. Next: backend
streaming events and UI integration. Live Docker checks remain an outstanding gate.

## Backend stage-streaming milestone — November 9, 2026 (IST)

Started from upstream beb0bc4 in a clean isolated checkout. Added POST /chat/stream
using SSE and the real async LangGraph update iterator. Events include started,
completed stages/attempt numbers, complete with the normal result/history, and
sanitized terminal errors. The synchronous endpoint remains intact. Disconnect
checks stop subsequent stages and close the graph iterator; synchronous calls
already running cannot be forcibly interrupted. This is not token/stdout streaming.

Validation:
- Fresh isolated environment installed requirements successfully.
- All 61 offline tests passed (7 new streaming tests).
- Covers SSE framing/IDs/order and final result via in-process HTTP; retry attempt
  counts; upstream/internal error sanitization; unsuccessful completion; HTTP 422;
  and cooperative cancellation after planning preventing generation/execution.
- pip check: no broken requirements. Compilation and whitespace checks passed.
- LangSmith Python 3.14 asyncio deprecation warning remains.
- No real network chunk timing, browser disconnect/proxy behavior, live provider
  call or live Docker execution was verified. No periodic keepalives or resume API.

Implementation commit: 7a4f262. Streaming contract/progress documentation is separate.
Next: React interface consuming stage events and rendering results/attempt history.
Durable cancellation/history, RAG, product GitHub integration, deployment and live
end-to-end gates still remain; November 16 is a target, not a verified completion.

## React streaming interface — November 10, 2026 (IST)

Started from upstream 8ec6f6d in a fresh isolated checkout. Added a responsive
React/Vite workspace with task submission, stage progress, execution stdout/stderr,
review feedback, generated file previews and per-attempt inspection. Added
AbortController-based Stop updates, clear errors, example prompts and single-run
submission guards. SSE parsing handles arbitrary byte chunks/Unicode, CRLF,
multiline data, terminal events, malformed payloads and premature disconnection.

Validation:
- All 14 frontend tests passed (2 test files, Vitest/Testing Library).
- Production Vite build passed; bundle approximately 72 KiB gzipped JavaScript.
- npm production dependency audit: 0 known vulnerabilities at check time.
- git diff --check passed.
- Browser desktop/mobile checks at default size and 390px width: task form and
  responsive layout inspected; a local test SSE backend returned a sample result;
  submission, final output and file switching verified in the actual browser.
- Test backend was a fixture, not FastAPI/LLM/Docker. No live model, generated-code
  execution or deployed proxy end-to-end check was performed. Existing 61 backend
  tests were not rerun because backend code did not change.

Implementation commit: 585c844. Setup/validation documentation follows separately.
Node dependencies are exact-pinned with a lockfile. Results are in-memory only;
production hosting, persistent history, real-model/Docker integration, RAG,
product GitHub integration and deployment remain. Stop updates does not guarantee
termination of already-running server operations. Next: repository-aware retrieval
and remaining integration gaps. November 16 remains an unverified target.

## Local retrieval foundation — November 11, 2026 (IST)

Started at upstream fced961 in a clean temporary checkout. Implemented local
lexical TF-IDF retrieval in the existing empty vector_store module. Deterministic
line chunks retain source provenance; query results include excerpts/citations.
Added POST /context/search for a server-configured RAG_ROOT only; disabled by
default. No client-controlled filesystem root, remote fetch or paid embedding call.

File policy excludes hidden/generated/dependency folders and symlinks; text type,
file bytes, corpus bytes, file count, chunk count and excerpt size are limited.
Search rebuilds per request to reflect edits. No secret-scanning or adversarial
filesystem-race guarantee is claimed, and no authentication/isolation was added.

Validation:
- All 74 backend tests passed (13 new retrieval/core/API tests).
- Fresh project requirements installed; pip check reports no broken requirements.
- Python compilation and git diff --check passed.
- Real repository smoke test indexed 63 files / 81 chunks without hitting limits;
  query validate_requirements returned the requirements validator among top 5 hits
  with relative file/line citations. Fixture ranking and provenance tests passed.
- LangSmith Python 3.14 asyncio deprecation warning remains.
- No live model, Docker or deployed-server verification. Frontend code was unchanged
  and its prior 14 tests were not rerun. Retrieval API tests use in-process HTTP.

Implementation commit: 0e3da0a. Retrieval/setup documentation is a separate commit.
This is retrieval infrastructure, not completed RAG: planner/coder prompt injection,
UI source display and generated-answer grounding are pending. No durable index or
semantic embeddings. Next: bounded context injection with source attribution.
