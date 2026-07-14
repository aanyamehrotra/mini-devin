import subprocess
import uuid
from pathlib import Path
from app.models.schemas import CodeResponse
from app.models.schemas import ExecutionResult

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
        result= subprocess.run(
            ["python3", "main.py"],
            capture_output=True,
            text=True,
            cwd=project,
            timeout=5
        )
        return ExecutionResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
        success=False,
        stdout="",
        stderr="Execution timed out after 5 seconds.",
        exit_code=-1,

    )
