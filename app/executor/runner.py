import subprocess
import uuid
from pathlib import Path

from app.models.schemas import ExecutionResult

def execute_code(code:str)-> ExecutionResult:
    workspace= Path("workspace")
    workspace.mkdir(exist_ok=True)
    project= workspace/str(uuid.uuid4())
    project.mkdir(parents=True, exist_ok=True)
    main_file= project/"main.py" 
    main_file.write_text(code)

    try:
        result= subprocess.run(
            ['python3', str(main_file)],
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
