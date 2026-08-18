import time
from groq import Groq, RateLimitError

from app.config import GROQ_API_KEY
from app.services.llm.base import BaseLLM


class GroqLLM(BaseLLM):

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def generate(self, prompt: str) -> str:

        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="groq/compound-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,
                )

                return response.choices[0].message.content

            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise

                retry_after = e.response.headers.get("retry-after")

                if retry_after:
                    wait_time = float(retry_after)
                else:
                    wait_time = 2 ** attempt

                print(
                    f"Rate limit reached. "
                    f"Retrying in {wait_time:.1f} seconds..."
                )

                time.sleep(wait_time)

        raise RuntimeError("LLM request failed after retries")