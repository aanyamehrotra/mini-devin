from fastapi import APIRouter

from app.models.schemas import ChatRequest
from app.agents.manager import run_agent

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest):
    return run_agent(request.prompt)