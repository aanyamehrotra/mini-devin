from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest
from app.services.llm.structured import AgentResponseError
from app.agents.manager import run_agent

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest):
    try:
        return run_agent(request.prompt)
    except AgentResponseError as error:
        raise HTTPException(
            status_code=502,
            detail={"error": error.kind, "stage": error.stage},
        ) from error