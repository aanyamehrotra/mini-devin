from pathlib import Path
import subprocess

def validate_in_docker(project_dir, python_files):
    abs_path = Path(project_dir).resolve()

    file_paths = [
        str(file.relative_to(project_dir))
        for file in python_files
    ]

    docker_command = [
        "docker",
        "run",
        "--rm",
        "--memory",
        "256m",
        "--cpus",
        "0.5",
        "--pids-limit",
        "64",
        "--security-opt",
        "no-new-privileges",
        "-v",
        f"{abs_path}:/app",
        "-w",
        "/app",
        "python:3.12-slim",
        "python",
        "-m",
        "py_compile",
        *file_paths,
    ]

    return subprocess.run(
        docker_command,
        capture_output=True,
        text=True,
        timeout=30,
    )

def run_in_docker(project_dir, entry_path):
    abs_path = Path(project_dir).resolve()

    container_command = (
        "if [ -s requirements.txt ]; then "
        "pip install --no-cache-dir -r requirements.txt || exit 1; "
        "fi; "
        f"python {entry_path}"
    )

    docker_command = [
        "docker",
        "run",
        "--rm",
        "--memory",
        "256m",
        "--cpus",
        "0.5",
        "--pids-limit",
        "64",
        "--security-opt",
        "no-new-privileges",
        "-v",
        f"{abs_path}:/app",
        "-w",
        "/app",
        "python:3.12-slim",
        "sh",
        "-c",
        container_command,
    ]

    result = subprocess.run(
        docker_command,
        capture_output=True,
        text=True,
        timeout=30,
    )

    return result