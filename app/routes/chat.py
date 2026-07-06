from fastapi import APIRouter

from app.models.schemas import ChatRequest
from app.services.gemini_service import generate_response

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest):

    answer = generate_response(request.prompt)

    return {
        "response": answer
    }