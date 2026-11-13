import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ACTIVE_LLM = os.getenv("ACTIVE_LLM", "groq")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_TIMEOUT = os.getenv("OLLAMA_TIMEOUT", "120")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
