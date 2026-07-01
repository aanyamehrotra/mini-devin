from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
app=FastAPI()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class ChatRequest(BaseModel):
    prompt:str 

@app.get('/')
def root():
    return {
        "message":'Mini-Devin is running'
    }

@app.post('/chat')
def chat(request:ChatRequest):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=request.prompt
    )
    return {
        'response': response.text
    }