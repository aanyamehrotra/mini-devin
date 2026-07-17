from pathlib import Path 
import subprocess

def run_in_docker(project_dir, entry_path):
    abs_path= Path(project_dir).resolve()
    docker_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{abs_path}:/app",
        "-w",
        "/app",
        "python:3.12-slim",
        "python",
        str(entry_path),
    ]
    result = subprocess.run(
    docker_command,
    capture_output=True,
    text=True,
    timeout=10,
    )
    return result