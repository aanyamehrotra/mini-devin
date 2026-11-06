"""Bounded Docker execution with explicit cleanup and no interpolated shell code."""

import logging
import os
from pathlib import Path
import subprocess
import uuid

logger = logging.getLogger(__name__)
TIMEOUT = 30
IMAGE = 'python:3.12-slim'


def _run(project_dir, command, *, network='none'):
    root = Path(project_dir).resolve()
    name = f'mini-devin-{uuid.uuid4().hex}'
    docker_command = [
        'docker', 'run', '--rm', '--name', name, '--init',
        '--memory', '256m', '--memory-swap', '256m', '--cpus', '0.5',
        '--pids-limit', '64', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--read-only',
        '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m,mode=1777',
        '--user', f'{os.getuid() or 65534}:{os.getgid() or 65534}', '--network', network,
        '-e', 'HOME=/tmp', '-e', 'PYTHONPYCACHEPREFIX=/tmp/pycache',
        '-e', 'PYTHONPATH=/tmp/deps',
        '-v', f'{root}:/app', '-w', '/app', IMAGE, *command,
    ]
    try:
        return subprocess.run(
            docker_command, capture_output=True, text=True, timeout=TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
    finally:
        # Killing the local Docker client alone does not guarantee container exit.
        try:
            cleanup = subprocess.run(
                ['docker', 'rm', '-f', name], capture_output=True, text=True, timeout=5,
            )
            if cleanup.returncode and 'No such container' not in cleanup.stderr:
                logger.warning('Container cleanup failed for %s', name)
        except (OSError, subprocess.TimeoutExpired):
            logger.warning('Container cleanup unavailable for %s', name)


def _relative_path(project_dir, path):
    root = Path(project_dir).resolve()
    candidate = Path(path)
    target = (root / candidate).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError('Docker file path must remain inside the project')
    return target.relative_to(root).as_posix()


def validate_in_docker(project_dir, python_files):
    root = Path(project_dir).resolve()
    # The executor passes file paths prefixed by project_dir; normalize them first.
    paths = [Path(file).resolve().relative_to(root).as_posix() for file in python_files]
    return _run(root, ['python', '-m', 'py_compile', *paths])


def run_in_docker(project_dir, entry_path):
    entry = _relative_path(project_dir, entry_path)
    requirements = Path(project_dir) / 'requirements.txt'
    if requirements.is_file() and requirements.stat().st_size:
        # The entry path is a positional argument, never part of shell syntax.
        script = (
            'python -m pip install --no-cache-dir --disable-pip-version-check '
            '--target /tmp/deps -r requirements.txt && exec python "$1"'
        )
        return _run(project_dir, ['sh', '-c', script, 'mini-devin', f'./{entry}'], network='bridge')
    return _run(project_dir, ['python', f'./{entry}'])
