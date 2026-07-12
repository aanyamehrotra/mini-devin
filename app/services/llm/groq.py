from groq import Groq

from app.config import GROQ_API_KEY
from app.services.llm.base import BaseLLM


class GroqLLM(BaseLLM):

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def generate(self, prompt: str) -> str:

        response = self.client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2,

        )

        return response.choices[0].message.content