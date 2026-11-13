# Final sprint: November 13–16, 2026

The user reaffirmed November 16 as the final target. Do not silently extend the
schedule, remove required features or equate mocked tests with full readiness.
Prioritize closing live integration and deployment gates over cosmetic work or
commit counts. Report completion against evidence, with exact remaining gaps.

| Date | Priority outcomes |
| --- | --- |
| Nov 13 | Product GitHub export; start real Docker checks; identify access/budget gaps |
| Nov 14 | Deployment configuration, health/readiness checks, execution safeguards |
| Nov 15 | Full workflow from UI through real provider/executor; repair issues; validate export in an authorized test repo |
| Nov 16 | Final regression, reproducible setup/demo, deployment verification where authorized, acceptance/gap report |

## Acceptance evidence

- Provider abstraction: working configured-provider request; report which providers
  were live-tested versus mocked. Do not claim all providers passed by extrapolation.
- Execution: real multi-file imports, dependencies, library validation, runtime and
  syntax errors, no-network runtime, timeout cleanup and bounded resource behavior.
- UI/API: actual streamed stages, complete results, retries and failure paths;
  opt-in context and readable source excerpts; cancelled-client limits documented.
- Retrieval: source/line provenance, bounded corpus/context, request opt-in, real
  retrieval-to-prompt flow. Attribution alone does not verify model correctness.
- GitHub: preview safety and scoped branch/draft-PR publication in an authorized
  repository; mocked calls and routine development pushes are distinct evidence.
- Deployment: reproducible artifacts, readiness checks, access protection, local
  startup and (only with account/budget authorization) real AWS verification.
- Final report: test results, known issues, what remains unimplemented/unverified,
  exact setup commands, commit references and no fabricated completion percentage.

## Current constraints

The user does not yet know their AWS account/region/budget. Use a no-spend approach:
prepare artifacts without provisioning paid services. An actual AWS launch still
requires an account/target and spending approval. This is not a reduction of scope;
it is an outstanding dependency and must appear in the final report if unresolved.
Docker Desktop has now been started and engine 29.6.1 responds. The previous missing
Docker socket blocker is cleared; real fixture validation is in progress.
Durable run history, browser GitHub export/OAuth and public deployment protections
must be evaluated explicitly rather than assumed complete from CLI functionality.
