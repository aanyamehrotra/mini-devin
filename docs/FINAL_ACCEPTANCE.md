# Final local acceptance — November 16, 2026

## Agreed scope

The user asked to complete Mini-Devin locally and explicitly kept AWS hosting
pending. This handoff is for a private, single-workspace local app and deployment
package. It is not a claim of a deployed AWS/public multi-tenant service or universal
correctness of generated programs.

## Delivered

| Area | Result |
| --- | --- |
| Orchestration | Real LangGraph state flow, bounded retries, rewrite feedback and attempts |
| Providers | Gemini/Groq/Ollama adapters; configured Groq tested live |
| Execution | Multi-file Python, read-only source, bounded scratch/dependencies/output, timeout cleanup |
| Resource controls | 1 MiB/100-file projects, bounded prompts, 20 source workspaces, one execution per server process |
| Frontend/API | React progress, output/errors, source files, attempt selection, same-origin production serving |
| History | Private SQLite archive, latest 100 completed runs, reload via authenticated API/UI |
| Retrieval | Opt-in bounded code/docs context across agents; relative source/line attribution |
| GitHub | Offline preview, explicit apply, isolated branch/folder, optional draft PR; real export verified |
| Deployment package | Setup/start scripts, pinned dependency snapshot, readiness/auth checks, Linux/private proxy templates |

## Final verification

- **128 offline backend tests passed**; 12 opt-in live cases skipped by default.
- **21 frontend tests passed**; production build succeeded.
- **10 real Docker tests passed**: dependencies, libraries, multi-file imports,
  syntax/runtime errors, output flood, disk exhaustion, read-only sources,
  no-network runtime and timeout cleanup.
- **2 real localhost HTTP tests passed**: production assets/health/auth, and an
  authenticated streamed Groq → agents → Docker workflow with opt-in retrieval,
  exact expected stdout, reviewer approval and saved-result reload.
- Real GitHub export created a fresh fixture branch/commit and **draft PR #1**:
  https://github.com/aanyamehrotra/mini-devin/pull/1 . It contains only disposable
  verification files under generated/318900087e4d47ef98b4b815f88cc12e/ and is not
  intended to be merged. No base-branch overwrite, force update or merge occurred.
- Python compilation, dependency check, shell syntax and whitespace checks passed.
- Tokens/keys were not printed or committed. GitHub verification used the existing
  authorized credential helper in memory; no GitHub token was saved in the repo.

The first history edit exposed an import error, which was corrected before the
full suite passed. The first bounded-dependency live test exposed tmpfs unmount
behavior; a bounded holder now preserves data across stages, and the final full
live suite passed. Tests are evidence for these cases, not an exhaustive proof.

## Run it

```sh
./scripts/setup-local.sh
# Configure the private .env using .env.example and start Docker.
./scripts/start-local.sh
```

Open http://127.0.0.1:8000. Use Load saved runs to restore completed work. Workspace
access takes a distinct shared token only when configured; never enter a provider
key into the browser. See DEPLOYMENT.md and HISTORY.md for setup/privacy limits.

## Explicit remaining limits

- AWS resources/hosting were not provisioned, per the user's decision. No spending
  approval/account was supplied and no cloud charges were initiated.
- Gemini/Ollama were offline-tested but not live-verified in the final Groq workflow.
- The final complete browser UI-to-model path was not browser-automated; real HTTP
  and component/stream tests cover it separately. Prior desktop/mobile visual checks
  used fixtures. Linux systemd/nginx templates were not installed on a Linux host.
- This is shared-workspace token access, not OAuth, tenant isolation or distributed
  scheduling. Use one API worker; separate processes have separate execution slots.
- Cancellation stops future stages; an already-running SDK/container operation can
  continue to its timeout. No durable graph resume or model-token/stdout streaming.
- History stores plaintext local prompts/code/context, with a 5 MiB result cap and
  automatic retention. It is not encrypted or a backup service; partial disconnected
  or upstream-failed requests are not archived as completed runs.
- GitHub export is CLI-based; no browser OAuth/export control. The live test used a
  harmless fixture, not an automatic publication of arbitrary generated code.
- Source attribution reports supplied context, not proven model usage/correctness.
- Python 3.14 emits a LangSmith asyncio deprecation warning; tests passed. Image
  digest pinning, distributed quotas and public-service security review remain
  future hardening; no public sandbox security certification is claimed.

No email was sent. Further AWS deployment or expanded production scope requires a
separate account/target/budget and verification pass.
