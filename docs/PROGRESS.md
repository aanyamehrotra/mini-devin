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
