from typing import List
from pydantic import BaseModel, Field, model_validator
from typing import Literal

class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1,max_length=20000)
    use_context: bool = Field(default=False, strict=True)
  
class Plan(BaseModel):
    goal: str
    features: List[str]
    files: List[str]
    technologies: List[str]
    steps: List[str]

class GeneratedFile(BaseModel):
    path: str = Field(max_length=400)
    content: str = Field(max_length=262144)

class CodeResponse(BaseModel):
    files: list[GeneratedFile] = Field(max_length=100)

    @model_validator(mode='after')
    def limit_total_content(self):
        if sum(len(file.content.encode('utf-8')) for file in self.files)>1024*1024:
            raise ValueError('Project content exceeds 1 MiB')
        return self

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