from pydantic import BaseModel


class GeneratedFile(BaseModel):
    path: str
    content: str