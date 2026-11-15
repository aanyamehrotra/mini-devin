# Mini-Devin

A local autonomous Python coding workspace: describe a task, follow planning/code/
execution/review stages, inspect generated files and retry attempts, and reload
completed runs later.

## Run locally

Requires Python 3.12+, a supported Node version (see frontend/package.json), Docker,
and a configured Groq, Gemini or Ollama provider.

```sh
./scripts/setup-local.sh
# Configure the ignored .env using .env.example; never commit keys.
# Start Docker Desktop / Docker Engine.
./scripts/start-local.sh
```

Open **http://127.0.0.1:8000**. The built React UI and FastAPI API share one origin.
If a workspace access token is configured, enter that separate token in Workspace
access. Provider keys stay in the backend; do not put them in the browser.

## Features

- LangGraph planner/coder/executor/reviewer loop with bounded rewrites.
- Gemini, Groq and Ollama adapters; configurable Groq model.
- Multi-file generation, private UUID workspaces and real Docker execution.
- Bounded output/runtime/dependency storage, read-only sources and execution serialization.
- React stage streaming, file/output/error previews and per-attempt inspection.
- Persistent local completed-run history with bounded retention.
- Opt-in local lexical retrieval with supplied source/line attribution.
- Preview-first GitHub CLI export to a fresh project folder/branch and optional draft PR.
- Shared-token API protection, health/readiness checks and private-host deployment templates.

## Guides and verification

- [Provider configuration](docs/PROVIDERS.md)
- [Frontend](docs/FRONTEND.md) and [streaming API](docs/STREAMING.md)
- [Saved history](docs/HISTORY.md)
- [Retrieval and context data sharing](docs/RETRIEVAL.md)
- [Execution limits](docs/EXECUTION.md)
- [GitHub export](docs/GITHUB_EXPORT.md)
- [Deployment preparation](docs/DEPLOYMENT.md)
- [Final acceptance and known limits](docs/FINAL_ACCEPTANCE.md)
- [Progress log](docs/PROGRESS.md)

```sh
.venv/bin/python -m unittest discover -s tests -v
npm test --prefix frontend
npm run build --prefix frontend
```

Live tests are opt-in and can consume model quota. The acceptance report separates
mocked, actual subprocess/container, HTTP and GitHub verification.

AWS hosting is explicitly pending at the user's request. This is a private/local
single-workspace application, not a public multi-tenant code-execution service.
Gemini/Ollama alternatives have offline coverage but were not live-verified in the
final Groq-based integration run. Generated programs still require review; passing
an agent review is not a universal correctness guarantee.
