# Single-host deployment preparation

This package runs the backend and built React UI from one origin. It is prepared
and locally tested, not deployed to AWS. No cloud resources, accounts, domains or
paid services were created. Actual AWS hosting still needs the user's account,
region, target and spending approval.

## Local production-style startup

Use Python 3.12+ and a Node version supported by frontend/package.json. Docker must
be installed and running. A dedicated Linux host can use Docker Engine; installing
Docker inside the API container or mounting the host Docker socket into a public
API container is not the supplied architecture.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
cd frontend
npm ci
npm run build
cd ..
```

requirements.lock records the fully resolved Python environment tested on macOS
Python 3.14 on November 14. It is a version snapshot, not a hash-verified multi-OS
lock; validate its wheels/compatibility on the actual Linux target. requirements.txt
remains the top-level dependency specification. npm uses its committed lockfile.

Configure the selected model in private environment variables or an ignored .env.
For a shared deployment, also set MINI_DEVIN_API_TOKEN to a randomly generated
secret of at least 32 characters, distinct from model/GitHub keys. One local method
to generate a value is `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`.
Put it in the private environment file; do not commit it or put it in frontend
build variables. The deployment preflight enforces the minimum length, not entropy.

```sh
.venv/bin/python -m app.tools.preflight --deployment
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Open http://127.0.0.1:8000. In Workspace access, enter the workspace token if one
is configured. The UI keeps it in memory and sends it as an Authorization header.
It is not your Groq/Gemini key and is not saved in browser storage.

## Routes and readiness

- `/` serves built index.html when available, otherwise the original JSON status.
- `/assets/*` serves only the built assets directory; environment files are not mounted.
- `/api/chat`, `/api/chat/stream`, `/api/context/search` support the production UI.
  Existing unprefixed routes remain for compatibility. The Vite dev proxy still works.
- If MINI_DEVIN_API_TOKEN is set, both route families require its Bearer token.
  The guard is pure ASGI so it does not buffer streamed bodies. Missing/wrong tokens
  return HTTP 401 before agent execution. Blank token is local development mode.
- `/health/live` reports the HTTP process is alive.
- `/health/ready` returns 200 or 503 based on provider configuration and a bounded
  Docker info check. It emits no secret values and is not cached. Provider presence
  is NOT a live provider authentication/availability check and does not incur a call.
- `preflight --deployment` additionally checks token length and built frontend files.
  A successful check does not establish full security or application correctness.

## Linux service templates

`deploy/mini-devin.service` assumes a dedicated `minidevin` account, checkout/venv
at /opt/mini-devin, and private environment file /etc/mini-devin.env. It starts only
after Docker and runs preflight first. Install templates only after adapting paths
and validating the target machine. They were not installed on the user's Mac.

The service identity needs Docker access and write access to its workspace/temp
directories. Docker group membership is effectively host-administrator access;
use a dedicated isolated machine, not a shared workstation containing unrelated
secrets. PrivateTmp is intentionally not enabled: bind-mounted temporary dependency
paths must be visible at the same host path to the Docker daemon. Do not enable
it without redesigning the shared paths.

`deploy/nginx.conf` is a PRIVATE loopback-only proxy example. It forwards the access
header, disables response buffering and allows long-lived stage streams. Linux
systemd/nginx configuration syntax and actual host startup have not been validated
on a Linux machine here. A shared token is not multi-user identity, rate limiting,
a tenant boundary or a public arbitrary-code execution security solution.

## AWS handoff (not executed)

After account/region/budget authorization, choose a dedicated Linux EC2 host with
sufficient memory/disk for Docker and dependency workloads. Do not assume free-tier
eligibility. Install Docker using its official platform instructions and validate
the application/service under the chosen unprivileged identity. Keep the backend
loopback-bound. Prefer private access/SSH tunneling during verification; restrict
inbound SSH to the approved administrator source. Security groups act as the EC2
network firewall. Public TLS/domain/routing requires a separate reviewed access
plan; the supplied nginx file does not expose a public endpoint.

Before calling deployment complete: validate the service/proxy, authenticated SSE,
actual configured provider, real generated-code execution, disk/output/concurrency
limits, secret handling, rollback/restart, and cloud costs on that actual target.
No AWS CLI provisioning command is automatically run by these artifacts.

References: [FastAPI static files](https://fastapi.tiangolo.com/tutorial/static-files/),
[Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/),
[EC2 security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html).

## Verified locally on November 14

111 offline backend tests and 20 frontend tests passed. Seven opt-in Docker tests
were not repeated for this change (they passed live November 13). Two NEW opt-in
real HTTP tests passed: built UI/assets and health endpoints, unauthorized rejection,
and authenticated SSE using the real Groq planner/coder/reviewer and Docker with
exact expected output. The local HTTP test server used an ephemeral port/token
and shut down afterward. This is not browser automation or an AWS deployment.
The first preflight observed Docker still starting and returned not ready; a later
fully initialized-engine check passed all four deployment checks.

To intentionally repeat live HTTP validation, build the frontend, start Docker,
configure a provider in the process environment, then run:

```sh
MINI_DEVIN_LIVE_HTTP=1 .venv/bin/python -m unittest tests.test_live_http -v
```

These tests call the configured real model and may consume provider quota. They
are skipped by the default offline suite. No emails are sent.
