# Mini-Devin: 15-day completion plan

Window: November 2–16, 2026. Daily development scheduled for 19:00 Asia/Kolkata.
This is a delivery target; discovered integration problems may require reprioritization.

The repository already includes Gemini/Groq abstraction, multi-file generation and
Docker execution. These need verification and hardening, not replacement.

| Day | Date | Deliverable |
| --- | --- | --- |
| 1 | Nov 2 | Baseline inspection, safe workspace paths, offline regression suite |
| 2 | Nov 3 | Ollama provider, provider configuration and mocked contract tests |
| 3 | Nov 4 | Structured model-output validation and predictable provider failures |
| 4 | Nov 5 | Docker hardening, container cleanup, timeouts and environment failures |
| 5 | Nov 6 | Multi-file validation, dependency handling and execution integration tests |
| 6 | Nov 7 | LangChain integration with provider adapters where useful |
| 7 | Nov 8 | LangGraph orchestration with bounded retries and recorded state |
| 8 | Nov 9 | Backend streaming events, cancellation and API tests |
| 9 | Nov 10 | React interface for prompts, live stages and execution output |
| 10 | Nov 11 | Attempt history, file previews and frontend integration checks |
| 11 | Nov 12 | Code/docs ingestion and local RAG retrieval with provenance |
| 12 | Nov 13 | Connect retrieval to planning and coding; retrieval tests |
| 13 | Nov 14 | Scoped GitHub integration and reviewable branch/PR workflow |
| 14 | Nov 15 | AWS deployment configuration, health checks and deployment guide |
| 15 | Nov 16 | End-to-end regression, documentation, demo and final gap report |

## Completion checks

- Offline automated tests do not require secrets or make provider calls.
- Each available provider has a consistent interface and useful failures.
- Generated paths remain within their workspace; runtime containment is tested.
- Multi-file projects and failed-attempt rewrites work end to end.
- UI renders streamed stages, errors and attempts.
- RAG citations identify the ingested source.
- GitHub writes use explicit repository scope and preserve unrelated changes.
- AWS readiness is documented; actual deployment depends on an available account,
  target and agreed costs. Do not claim a deployment without verifying it.
- Every daily report distinguishes automated checks, manual checks and blocked checks.

## Actual status — November 8

Provider abstraction, strict agent-output validation, workspace protection,
requirements restrictions and Docker hardening code are delivered. Multi-file and
container logic have offline coverage; live Docker integration remains unverified.
LangGraph orchestration with request-local history is delivered using LangChain
Core runnables. Migration to LangChain chat-model adapters is not implemented.
Streaming API/cancellation, React UI, RAG, product GitHub integration, deployment
and full end-to-end verification remain. The original dates are targets; the
remaining scope is not yet verified complete for November 16.

## Incremental status — November 11

React stage streaming, output/file previews and attempt inspection are delivered
with fixture-backed browser checks. Local code/docs retrieval search is delivered
with file/line provenance and bounded ingestion. It is not yet connected to agent
prompts or the UI. Persistent history, live model/Docker end-to-end validation,
product GitHub integration and AWS deployment remain outstanding. Original dates
remain delivery targets rather than a statement that these gates have passed.
