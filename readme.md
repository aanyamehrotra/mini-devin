# Mini-Devin

An autonomous Python coding workspace: describe a task, follow planning/code/
execution/review stages, inspect generated files and retry attempts, and reload
completed runs later.

## Hosted application

**[Open Mini-Devin](https://mini-devin-13-55-65-113.sslip.io)**

Hosted on AWS in Sydney (`ap-southeast-2`). Visitors can run two real Python
examples **without signing in or entering a token**. Demo access is limited to
three runs per visitor/network per UTC day, twenty shared runs per UTC day,
one active demo at a time, and a minute between runs. Limits survive service
restarts; failed and disconnected attempts count too.

For full access, **ask the project owner for a workspace access token**, then
[open the private workspace](https://mini-devin-13-55-65-113.sslip.io/workspace).
Custom prompts and saved history remain token protected. Public demo results
are never added to private history. Provider keys and the workspace token are
not published. See [public demo setup and limits](docs/PUBLIC_DEMO.md).

Verified on November 16, 2026: trusted HTTPS, production UI/assets, Docker readiness,
unauthorized-request rejection, a real Groq → planner/coder → Docker → reviewer
streamed run, and saved-result reload.

This deployment uses Free plan credits, not permanently free compute. The project
was verified as `FREE / ACTIVE` with US$100 remaining credits before provisioning;
its plan expires May 16, 2027, or earlier if credits run out. No Paid plan upgrade
was performed. AWS closes the Free plan project when its free period or credits
end. See [AWS Free plan terms](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).

The free `sslip.io` hostname depends on the server's current public IP. A stop/start
can change that IP and require a hostname/configuration update.

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

The hosted app is a token-protected single-workspace deployment, not a public
multi-tenant code-execution service. Earlier local acceptance documents describe
the pre-deployment state; the hosted verification above supersedes their AWS-pending status.
Gemini/Ollama alternatives have offline coverage but were not live-verified in the
final Groq-based integration run. Generated programs still require review; passing
an agent review is not a universal correctness guarantee.
