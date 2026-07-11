from fastapi import APIRouter

from app.models.schemas import ChatRequest
from app.agents.planner import plan_task
from app.agents.coder import write_code
from app.executor.runner import execute_code
from app.agents.reviewer import review_code
from app.agents.coder import rewrite_code

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest):
    plan= plan_task(request.prompt)
    attempts=[]
    MAX_RETRIES = 3
    for i in range(MAX_RETRIES):
        if i == 0:
            code = write_code(plan)
        else:
            code = rewrite_code(
                plan,
                code,
                review
            )
        execution= execute_code(code)
        review= review_code(plan,code,execution)
        attempts.append({
    "attempt": i+1,
    "execution": execution,
    "review": review,
    "code":code,
    "success": execution.success
    })
        if review == "SUCCESS":
            break 
    return {
        "plan": plan,
        'code':code,
        'execution': execution,
        'review': review,
        "attempts":attempts
    }
    