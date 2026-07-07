from fastapi import APIRouter

from app.models.schemas import ChatRequest
from app.agents.planner import plan_task
from app.agents.coder import generate_code

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest):
    plan= plan_task(request.prompt)
    code = generate_code(plan)
    return {
        "plan": plan,
        'code':code
    }
    