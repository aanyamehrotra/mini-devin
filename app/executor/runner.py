import platform
import subprocess
import uuid
import sys
from pathlib import Path

from app.models.schemas import CodeResponse, ExecutionResult


def execute_code(project: CodeResponse) -> ExecutionResult:
    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)

    project_dir = workspace / str(uuid.uuid4())
    project_dir.mkdir(parents=True, exist_ok=True)

    for file in project.files:
        file_path = project_dir / file.path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file.content)

    venv_dir = project_dir / "venv"

    try:

        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=True,
            text=True,
        )
        print("venv exists:", venv_dir.exists())
        print("contents:", list(project_dir.iterdir()))


        if platform.system() == "Windows":
            python_executable = (venv_dir / "bin" / "python.exe").resolve()
        else:
            python_executable =(venv_dir / "bin" / "python").resolve()
        print("Python executable:", python_executable)
        print("Exists:", python_executable.exists())
        requirements_file = (project_dir / "requirements.txt").resolve()

        if requirements_file.exists():
            subprocess.run(
                [
                    str(python_executable),
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirements_file),
                ],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        ENTRY_FILES = {"main.py", "app.py", "run.py", "server.py", "index.py"}
        entry_path = None
        for entry in ENTRY_FILES:
            match = next(project_dir.rglob(entry), None)
            if match:
                entry_path = match.relative_to(project_dir)
                break
        compile_result = subprocess.run(
        [
            str(python_executable),
            "-m",
            "py_compile",
            str(entry_path),
        ],
        capture_output=True,
        text=True,
        cwd=project_dir,
        )
        if compile_result.returncode != 0:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=compile_result.stderr,
                exit_code=compile_result.returncode,
            )
        result = subprocess.run(
            [str(python_executable), str(entry_path)],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=5,
        )
        if entry_path is None:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="No executable entry point found (expected one of: main.py, app.py, run.py, server.py, index.py).",
                exit_code=-1,
            )

        return ExecutionResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )

    except subprocess.CalledProcessError as e:
        return ExecutionResult(
            success=False,
            stdout=e.stdout or "",
            stderr=e.stderr or str(e),
            exit_code=e.returncode,
        )

    except subprocess.TimeoutExpired:

        uses_input = any(
            "input(" in file.content
            for file in project.files
        )

        if uses_input:
            error = (
                "Program requires interactive user input. "
                "Autonomous execution does not provide stdin. "
                "Rewrite the program to remove input() and use sample values instead."
            )
        else:
            error = "Execution timed out after 5 seconds."

        return ExecutionResult(
            success=False,
            stdout="",
            stderr=error,
            exit_code=-1,
        )