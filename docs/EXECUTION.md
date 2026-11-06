# Docker execution and current limits

Install Docker and start its service before running generated Python projects.
`docker info` must succeed; `python:3.12-slim` must be available or pullable.
Mini-Devin never falls back to executing generated code on the host.

Each validation/execution container has a UUID name, a 30-second client timeout,
256 MiB memory/swap limit, half a CPU and 64-process limit. Containers drop all
capabilities, use no-new-privileges, an init process and a read-only root filesystem.
The container user matches the host UID/GID; root hosts fall back to UID/GID 65534.
The mounted workspace must therefore be readable and writable by that identity.
A 128 MiB temporary filesystem provides scratch space and Python bytecode storage.

Syntax validation and projects with no nonempty root requirements.txt run with
network disabled. Projects with requirements.txt install into /tmp/deps using pip
and currently run in the SAME network-enabled container. This compatibility path
is not network isolation for dependency projects. Dependency installation and
execution need separate stages before stronger network isolation can be claimed.

Entry paths are checked to remain in the project. Runtime paths are passed as
arguments (including through a positional shell parameter when installing packages),
so spaces and shell metacharacters do not become shell instructions. The generated
workspace remains writable to support project output; the host Docker socket and
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

Still outstanding: bounded stdout/stderr capture, separate dependency execution,
image digest pinning, broader environment classification, workspace retention and
live container tests. This is an incremental Docker hardening change, not a complete
security boundary for public arbitrary-code execution.

Docker flag behavior: [official docker run reference](https://docs.docker.com/reference/cli/docker/container/run/).
