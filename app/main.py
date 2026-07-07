from fastapi import FastAPI
from app.routes.chat import router as chat_router

app = FastAPI()
@app.get("/")
def root():
    return {
        "message": "Mini-Devin is running"
    }

app.include_router(chat_router)