# Docker execution and current limits

Install Docker and start its service before running generated Python projects.
`docker info` must succeed; `python:3.12-slim` must be available or pullable.
Mini-Devin never falls back to executing generated code on the host.

Each validation/execution container has a UUID name, a 30-second client timeout,
256 MiB memory/swap limit, half a CPU and 64-process limit. Containers drop all
capabilities, use no-new-privileges, an init process and a read-only root filesystem.
The container user matches the host UID/GID; root hosts fall back to UID/GID 65534.
The mounted source must be readable by that identity; runtime writes use bounded scratch storage.
A 128 MiB temporary filesystem provides scratch space and Python bytecode storage.

Syntax validation and application execution run with network disabled. Projects
with a nonempty root requirements.txt first use a separate network-enabled pip
container. A bounded tmpfs-backed Docker volume transfers dependencies into a read-only runtime mount,
with its mount lifetime held across stages (see the final policy below).
The generated application is not launched if installation fails. Both stages use
the same Python image and each has a separate 30-second timeout.

Installation requests wheels only (--only-binary=:all:) and skips bytecode
compilation. Packages lacking compatible wheels may fail. Requirements accept package names, extras and version constraints only. Local
paths, direct URLs, editable installs, nested requirement files, pip options and
environment markers are rejected before installation. Comments are supported;
comment-only files skip installation. Invalid files return InvalidRequirements.
This restricted syntax does not establish that a package is trustworthy. Do not
provide the installer credentials. The current dependency volume has a 128 MiB quota.

Entry paths are checked to remain in the project. Runtime paths are passed directly as
arguments,
so spaces and shell metacharacters do not become shell instructions. The generated
source is now read-only and runtime files use /tmp/project; the host Docker socket and
host credentials are not mounted.

The runner attempts `docker rm -f` on its unique container name after every run,
including timeouts. Cleanup is bounded by five seconds; failures log a warning
rather than replacing the original execution outcome. Cleanup cannot be guaranteed
when the Docker service is unreachable. A Docker startup exit status of 125 and
host process-start errors return ExecutionEnvironment rather than SyntaxError.

## Validation and remaining work

Offline tests mock subprocess calls and verify cleanup/error branches and execution
arguments. They do not establish actual kernel isolation. Run real container
checks before deployment: successful single/multi-file projects, dependency imports,
syntax/runtime errors, timeouts with no surviving containers, denied network access,
and workspace permissions on the target OS.

Current remaining hardening includes image digest pinning, broader environment classification
and multi-process scheduling. The final policy below supersedes the earlier storage design. This is an incremental Docker hardening change, not a complete
security boundary for public arbitrary-code execution.

Docker flag behavior: [official docker run reference](https://docs.docker.com/reference/cli/docker/container/run/).

Projects with no Python files return UnsupportedProject instead of successful
library validation. Python libraries without a recognized entry file are compiled
but not executed. Nested entry discovery is deterministic. Offline multi-file tests
verify file writes, entry selection, failure routing and distinct workspaces; they
do not run generated imports in a real container.

## Real Docker fixture verification — November 13

Docker Desktop engine 29.6.1 was started and the official python:3.12-slim image
pulled. All seven opt-in tests in tests/test_live_docker.py passed: nested imports,
module/library compilation, syntax and runtime error classification, no-network
runtime, installed dependency imports, and a 30-second timeout with no surviving
new container. These are real engine checks, not mocked subprocess results.

To run them intentionally after starting Docker and pulling the image:

```sh
MINI_DEVIN_LIVE_DOCKER=1 .venv/bin/python -m unittest tests.test_live_docker -v
```

The default suite skips them. Tests do not call a model provider. They do not prove
all resource/escape protections, bounded output handling, or public deployment
safety. Those remain separate gates. The live run took about 47 seconds.

## Bounded output — November 15

The Docker client and cleanup subprocess now use a selector-based reader retaining
at most 256 KiB of combined raw stdout/stderr. On overflow the client is killed,
OutputLimitExceeded is returned, and the existing forced container cleanup runs.
UTF-8 decoding replaces invalid sequences. Timeout handling kills/reaps the client
before propagating its timeout. Diagnostic text is separate from the raw-byte budget.
This bounds retained output, not workload disk usage or concurrent job count.
Real host-process flood/timeout tests and a real Docker output-flood test passed.

## Final storage/concurrency policy — November 16

Current execution mounts generated source read-only at /source, copies it into
/tmp/project inside the 128 MiB runtime tmpfs and runs there. Generated runtime
writes no longer use a writable host workspace. Stdout/stderr remain capped at
256 KiB combined raw bytes. Docker daemon log storage is disabled for these jobs.

Dependency installation uses a separate 128 MiB tmpfs-backed Docker volume. A
small, networkless, read-only holder container keeps that mount alive across the
installer and runtime; otherwise local-driver tmpfs data disappears at unmount.
The runtime sees dependencies read-only. Both holder and volume are removed on
context exit. A real dependency install/import validated this lifecycle after an
initial live test exposed the missing-holder issue.

The backend serializes actual Docker execution with a nonblocking process-local
semaphore. Busy executions return an environment failure; no hidden queue is added.
Use the supplied single-worker deployment. Multiple server processes/instances
have independent limits; this is not a distributed scheduler.

Generated projects are limited to 100 files, 1 MiB combined UTF-8 content and
262,144 characters per file. Requests allow up to 20,000 prompt characters. Source
workspace retention prunes only our UUID directories beyond the latest 20 and
preserves unrelated directories. The history database has separate bounded retention.
These are local single-workspace controls, not a complete adversarial multi-tenant
security certification. Model calls already in progress still cannot be force-cancelled.

Ten real Docker checks passed in the final run: dependencies, nested imports,
library validation, syntax/runtime errors, network denial, source immutability,
bounded disk, bounded output and timeout cleanup. A real authenticated HTTP/model/
retrieval/history workflow also passed. See FINAL_ACCEPTANCE.md for exact scope.
