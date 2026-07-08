from typing import List
from pydantic import BaseModel

class ChatRequest(BaseModel):
    prompt: str
  
class Plan(BaseModel):
    goal: str
    features: List[str]
    files: List[str]
    technologies: List[str]
    steps: List[str]

class ExecutionResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int