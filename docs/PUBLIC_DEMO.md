# Public portfolio demo

The hosted root page is a no-token demo. Choose Fibonacci or a sample CSV summary,
then Run live demo. The actual planner, coder, Docker executor and reviewer run;
this is not a prerecorded result. The interface explains access limits when an
example is selected or a run starts and tells visitors to ask the project owner
for a workspace access token for full access.

## Boundaries

- Server accepts only preset task IDs; arbitrary prompts and retrieval are rejected.
- Three attempts per visitor network per UTC day, twenty attempts shared per day,
  one active demo, and a 60-second per-network cooldown. Shared networks share
  an allowance. IPv6 addresses are grouped by /64.
- SQLite reserves attempts atomically before starting work. Counts persist across
  restarts. Failed/disconnected runs still count; a disconnected client cannot
  free the active slot while its worker continues. An interrupted process leaves
  a conservative 10-minute lease before another demo can start.
- Each demo makes one generation/execution attempt, with no agent rewrite loop.
  Groq calls have a 4096-token output cap, a 30-second SDK timeout, and no retries.
  Public examples cannot install third-party packages. Runtime execution remains
  networkless with the existing Docker CPU, memory, disk, process and time limits.
- Public results stream only to the requesting browser and are not archived. Private
  history, context search and custom-prompt endpoints still require the owner token.
- Quota storage contains keyed hashes of network addresses, not raw IPs. Caddy
  access logs separately record request addresses under local log rotation.
- Quota storage failure closes demo access rather than permitting unmetered runs.

These controls bound demo usage; they do not identify individual people. A caller
with multiple networks can consume more than one visitor allowance, but the shared
20-attempt cap still applies. Owner credentials must stay private. The dedicated
Docker host is not a certified public multi-tenant sandbox.

## Enable on a dedicated host

Keep MINI_DEVIN_API_TOKEN set to a random private value of at least 32 characters.
Set MINI_DEVIN_PUBLIC_DEMO=1 and MINI_DEVIN_DEMO_DB to a private writable SQLite
path. The demo fails closed if the owner token is absent/short or if disabled.
Build the hosted UI with `VITE_PUBLIC_DEMO=true npm run build --prefix frontend`.
The `/workspace` page serves the owner interface; all its APIs retain Bearer auth.
Do not put the owner token or provider credentials into Vite build variables.

Use one API process/worker. The SQLite quota also enforces cross-thread admission.
Caddy must be the only ingress to the loopback-bound API: its derived client
address is used for quotas. Never expose Uvicorn directly or trust arbitrary
proxy headers from public clients.

Disable the public endpoint with MINI_DEVIN_PUBLIC_DEMO=0 and restart the service.
A normal frontend build without VITE_PUBLIC_DEMO preserves local workspace behavior.
The AWS project remains on its Free plan; no new infrastructure is required.

## Portfolio walkthroughs

The public page offers three explicitly recorded examples without using any live
quota: a CSV quality audit, a multi-file log analyser and a seeded bug repair.
These contain only public fixtures, source and actual execution results. The repair
recording identifies its seeded first failure. Visitors can inspect files, compare
attempts, review timings, copy code and download a safe ZIP. No owner history is
used to populate these recordings.

Live presets also include the CSV audit, log analysis and average fix. Shared live
requests have a one-minute global cooldown to respect the free provider's token
rate limit, in addition to the existing daily/per-network and concurrency limits.
A cooldown or quota failure points visitors to the always-available walkthroughs.
