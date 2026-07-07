from fastapi import APIRouter

from app.models.schemas import ChatRequest
from app.agents.planner import plan_task

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest):
    plan= plan_task(request.prompt)

    return {
        "plan": plan
    }
    