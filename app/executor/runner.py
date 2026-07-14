import subprocess
import uuid
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

    try:
        result = subprocess.run(
            ["python3", "main.py"],
            capture_output=True,
            text=True,
            cwd=project_dir,      # ✅ Fixed
            timeout=5
        )

        return ExecutionResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
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