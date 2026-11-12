# Streaming agent progress

POST `/chat/stream` with the same JSON body as `/chat`:

```sh
curl -N -X POST http://localhost:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Print hello"}'
```

The response uses `text/event-stream` (SSE), `Cache-Control: no-cache` and
`X-Accel-Buffering: no`. Use streaming fetch rather than browser EventSource,
which does not support this POST body. Proxies may still need buffering settings.
Each event is terminated by a blank line and has a request-local sequential ID:

```text
id: 2
event: stage
data: {"stage":"plan","status":"completed"}

```

## Event contract

| Event | Data | Meaning |
| --- | --- | --- |
| started | status: running | Request accepted; generation has not necessarily succeeded. |
| stage | stage, status: completed, optional attempt | One graph node completed. |
| complete | success, result | Graph finished; result has the normal plan/code/execution/review/attempts fields. |
| error | error, optional stage | Terminal upstream or internal failure; no complete event follows. |
| cancelled | reason: client_disconnected | Cooperative stop; a disconnected client may not receive it. |

Stages are plan, generate, execute and review. Generate covers both initial code
and rewrites. Attempt is omitted for plan and starts at 1 for execution cycles.
Stage events contain progress metadata; generated code and complete attempt
history arrive in the final result. This is stage streaming, not live model tokens
or live stdout. `complete.success=false` means the workflow finished unsuccessfully,
including retry exhaustion or an execution-environment failure.

Invalid input returns HTTP 422 before streaming. Once streaming has started, an
upstream failure produces an error EVENT within HTTP 200; clients must inspect
event types, not just HTTP status. Structured failures retain error/stage values
from `/chat`; unexpected exceptions use internal_error without raw exception text.
The existing synchronous `/chat` endpoint remains available with HTTP 502 errors.

## Cancellation and limits

Abort the fetch to close the connection. The streaming manager checks disconnection
between graph stages and closes its async graph iterator on exit. It cannot forcibly
interrupt synchronous SDK requests or Docker subprocesses already running in worker
threads. Those operations can continue until their own completion/timeout. There is
no durable run ID, separate cancel endpoint or resume support. Event IDs reset on
each request and do not support Last-Event-ID replay.

No periodic keepalive is emitted during a long stage yet. Configure proxy timeouts
accordingly. Frontend rendering, real browser disconnect behavior, deployed proxy
buffering, live LLM output and live Docker enforcement still need integration tests.

## Verified behavior

The offline suite runs the real async LangGraph flow with stubbed provider and
executor results. It covers in-process HTTP SSE framing, ordering, IDs, retry attempt
numbers, final result serialization, safe provider/internal failures, unsuccessful
completion, invalid input, and cancellation between stages preventing code generation.
TestClient buffers responses; those HTTP tests alone do not prove network chunk
arrival timing or an in-flight operation being stopped.

Reference: [LangGraph streaming](https://docs.langchain.com/oss/python/langgraph/streaming).

## Optional retrieval attribution

The request may include `use_context:true` (strict boolean, default false). Enabled
runs add `context` to the final result with status and bounded source excerpts.
Progress event types/order remain the same; retrieval happens once during planning.
See [retrieval configuration and provider data sharing](RETRIEVAL.md).
