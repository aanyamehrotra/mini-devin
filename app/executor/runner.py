import platform
import subprocess
import uuid
import sys
import time
from pathlib import Path

from app.models.schemas import CodeResponse, ExecutionResult


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

    venv_dir = project_dir / "venv"

    try:

        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True,
            capture_output=True,
            text=True,
        )

        if platform.system() == "Windows":
            python_executable = (venv_dir / "Scripts" / "python.exe").resolve()
        else:
            python_executable =(venv_dir / "bin" / "python").resolve()

        requirements_file = project_dir / "requirements.txt"

        requirements_file = project_dir / "requirements.txt"

        if requirements_file.exists() and requirements_file.read_text().strip():
            subprocess.run(
                [
                    str(python_executable),
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    "requirements.txt",
                ],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            )
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

                    if venv_dir in match.parents:
                        continue

                    entry_path = match.relative_to(project_dir)
                    break

                if entry_path is not None:
                    break
            
        if entry_path is None:
            
            for python_file in python_files:
                compile_result = subprocess.run(
                    [
                        str(python_executable),
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
                            time.perf_counter() - start_time, 3
                        ),
                        error_type="SyntaxError",
                    )
            execution_time = round(time.perf_counter() - start_time, 3)
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="No executable entry point found.",
                exit_code=-1,
                execution_time=execution_time,
                error_type="EntryPointError",
            )
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
            execution_time = round(time.perf_counter() - start_time, 3)

            return ExecutionResult(
                success=False,
                stdout="",
                stderr=compile_result.stderr,
                exit_code=compile_result.returncode,
                execution_time=execution_time,
                error_type="SyntaxError",
            )
       
        result = subprocess.run(
            [str(python_executable), str(entry_path)],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=5,
        )
        execution_time = round(time.perf_counter() - start_time, 3)
        
        error_type = None
        if result.returncode != 0:
            error_type = classify_error(result.stderr)

        execution_time = round(time.perf_counter()-start_time,3)

        return ExecutionResult(
        success=result.returncode == 0,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
        execution_time=execution_time,
        error_type=error_type,
    )

    except subprocess.CalledProcessError as e:
        execution_time = round(time.perf_counter() - start_time, 3)
        error_type = classify_error(e.stderr or "")
        return ExecutionResult(
            success=False,
            stdout=e.stdout or "",
            stderr=e.stderr or str(e),
            exit_code=e.returncode,
            execution_time=execution_time,
            error_type=error_type,
        )

    except subprocess.TimeoutExpired as e:
        error_type = "Timeout"
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
        execution_time = round(time.perf_counter() - start_time, 3)
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=error,
            exit_code=-1,
            execution_time=execution_time,
            error_type=error_type
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