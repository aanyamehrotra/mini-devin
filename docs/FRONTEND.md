# React coding workspace

The React/Vite interface submits tasks to the streaming backend, shows completed
workflow stages, and renders execution output, errors, review feedback, generated
files and per-attempt results. Examples fill the prompt; they do not trigger a run.
Generated source is displayed as text, never executed by the browser.

## Local setup

Start the configured FastAPI backend in the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Configure the selected model in the root environment as described in
[provider setup](PROVIDERS.md). Docker must be running for real execution.
No provider keys belong in frontend source or Vite variables.

In a second terminal, with Node 20.19+, Node 22.13+ or Node 24+:

```sh
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. The development server proxies `/api/chat/stream` to
`http://127.0.0.1:8000/chat/stream`. To change the backend target, set
`MINI_DEVIN_API_TARGET` when starting Vite. The UI uses same-origin fetch; no broad
CORS permission is added. Exact dependencies and the npm lockfile are committed.

## Usage and limits

- Describe a Python task and select Build project. Duplicate submissions are
  disabled while a request runs. Progress updates show completed stages only.
- When finished, inspect the output and review. Select an attempt to inspect its
  code/errors, or choose a file tab to view its source.
- Stop updates aborts the browser fetch. Work already running may still finish;
  see the backend [cancellation limits](STREAMING.md).
- Results/history live in memory and disappear on reload; there is no durable
  session store, downloaded project bundle, authentication or provider settings UI.
- This is stage streaming, not model token or live stdout streaming.
- Typography optionally loads Google Fonts; local fallback fonts work without it.

## Tests and production build

```sh
npm test
npm run build
npm audit --omit=dev
```

The 17 frontend tests cover fragmented/Unicode/CRLF/multiline SSE data, terminal
and transport errors, premature EOF, invalid results, aborts, example prompts,
result rendering, file/attempt selection, provider failures, stopping updates, reference opt-in and source display.
Component tests mock the transport; parser tests use ReadableStream byte fixtures.
Browser checks used a local mock SSE backend to inspect desktop/mobile layout,
submit a sample and switch generated files. They do not verify live model output
or Docker. Existing 61 backend tests were not rerun for this frontend-only change.

`npm run build` writes ignored `dist/` assets. Production hosting must serve the
assets and reverse-proxy `/api/*` to FastAPI with the `/api` prefix removed and
streaming buffering disabled. Vite's development proxy does NOT apply to a static
production build or `vite preview`. No site was deployed by this milestone.
Authentication, deployed browser end-to-end checks and durable history remain
future work. Do not expose the arbitrary-code backend publicly without its
remaining execution and access-control work.

## Optional references

Use project references is off by default. Enable it only to send excerpts from the
backend's configured RAG_ROOT corpus to the selected model provider. Results show
expandable References supplied with citation ranges and shortened-excerpt labels.
Unavailable/no-match states are explicit. Source attribution does not establish
that the model used a reference correctly. See [retrieval](RETRIEVAL.md).
