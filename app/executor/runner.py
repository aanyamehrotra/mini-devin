import subprocess
import uuid
import time
from pathlib import Path

from app.models.schemas import CodeResponse, ExecutionResult
from app.executor.docker_runner import run_in_docker


def execute_code(project: CodeResponse) -> ExecutionResult:
    start_time = time.perf_counter()

    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)

    project_dir = workspace / str(uuid.uuid4())
    project_dir.mkdir(parents=True, exist_ok=True)

    for file in project.files:
        file_path = project_dir / file.path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file.content)

    try:
        ENTRY_FILES = [
            "main.py",
            "app.py",
            "run.py",
            "server.py",
            "index.py",
        ]

        entry_path = None

        for entry in ENTRY_FILES:
            candidate = project_dir / entry

            if candidate.is_file():
                entry_path = candidate.relative_to(project_dir)
                break

        if entry_path is None:
            for entry in ENTRY_FILES:
                for match in project_dir.rglob(entry):
                    entry_path = match.relative_to(project_dir)
                    break

                if entry_path is not None:
                    break

        python_files = list(project_dir.rglob("*.py"))

        if entry_path is None:
            for python_file in python_files:
                compile_result = subprocess.run(
                    [
                        "python3",
                        "-m",
                        "py_compile",
                        str(python_file.relative_to(project_dir)),
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
                        execution_time=round(
                            time.perf_counter() - start_time,
                            3,
                        ),
                        error_type="SyntaxError",
                    )

            execution_time = round(
                time.perf_counter() - start_time,
                3,
            )

            return ExecutionResult(
                success=True,
                stdout=(
                    "All Python files compiled successfully. "
                    "No executable entry point found; "
                    "project validated as a module/library."
                ),
                stderr="",
                exit_code=0,
                execution_time=execution_time,
                error_type=None,
            )

        compile_result = subprocess.run(
            [
                "python3",
                "-m",
                "py_compile",
                str(entry_path),
            ],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )

        if compile_result.returncode != 0:
            execution_time = round(
                time.perf_counter() - start_time,
                3,
            )

            return ExecutionResult(
                success=False,
                stdout="",
                stderr=compile_result.stderr,
                exit_code=compile_result.returncode,
                execution_time=execution_time,
                error_type="SyntaxError",
            )

        result = run_in_docker(
            project_dir,
            entry_path,
        )

        error_type = None

        if result.returncode != 0:
            error_type = classify_error(result.stderr)

        execution_time = round(
            time.perf_counter() - start_time,
            3,
        )

        return ExecutionResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            execution_time=execution_time,
            error_type=error_type,
        )

    except subprocess.CalledProcessError as e:
        execution_time = round(
            time.perf_counter() - start_time,
            3,
        )

        error_type = classify_error(e.stderr or "")

        return ExecutionResult(
            success=False,
            stdout=e.stdout or "",
            stderr=e.stderr or str(e),
            exit_code=e.returncode,
            execution_time=execution_time,
            error_type=error_type,
        )

    except subprocess.TimeoutExpired:
        execution_time = round(
            time.perf_counter() - start_time,
            3,
        )

        uses_input = any(
            "input(" in file.content
            for file in project.files
        )

        if uses_input:
            error = (
                "Program requires interactive user input. "
                "Autonomous execution does not provide stdin. "
                "Rewrite the program to remove input() "
                "and use sample values instead."
            )
        else:
            error = "Docker execution timed out after 30 seconds."

        return ExecutionResult(
            success=False,
            stdout="",
            stderr=error,
            exit_code=-1,
            execution_time=execution_time,
            error_type="Timeout",
        )


def classify_error(stderr: str) -> str | None:
    if "SyntaxError" in stderr:
        return "SyntaxError"

    if "ModuleNotFoundError" in stderr:
        return "ModuleNotFoundError"

    if "ImportError" in stderr:
        return "ImportError"

    if "FileNotFoundError" in stderr:
        return "FileNotFoundError"

    if "NameError" in stderr:
        return "NameError"

    if "TypeError" in stderr:
        return "TypeError"

    if "ValueError" in stderr:
        return "ValueError"

    if "TimeoutExpired" in stderr:
        return "Timeout"

    return None