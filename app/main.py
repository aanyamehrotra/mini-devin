from fastapi import FastAPI
from google import genai

from app.models.schemas import ChatRequest
from app.config import GEMINI_API_KEY

app = FastAPI()

client = genai.Client(api_key=GEMINI_API_KEY)


@app.get("/")
def root():
    return {
        "message": "Mini-Devin is running"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=request.prompt
    )

    return {
        "response": response.text
    }