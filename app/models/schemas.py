from typing import List
from pydantic import BaseModel
from typing import Literal

class ChatRequest(BaseModel):
    prompt: str
  
class Plan(BaseModel):
    goal: str
    features: List[str]
    files: List[str]
    technologies: List[str]
    steps: List[str]

class GeneratedFile(BaseModel):
    path: str
    content: str

class CodeResponse(BaseModel):
    files: list[GeneratedFile]

class ExecutionResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    error_type: str | None = None

class ReviewResult(BaseModel):
    success: bool
    feedback: str
    failure_source: Literal[
        "code",
        "execution_environment",
        "requirements",
    ] | None = None