from app.config import ACTIVE_LLM


def get_llm():

    provider = ACTIVE_LLM.lower()

    if provider == "groq":
        from app.services.llm.groq import GroqLLM
        return GroqLLM()

    elif provider == "gemini":
        from app.services.llm.gemini import GeminiLLM
        return GeminiLLM()

    raise ValueError(f"Unsupported provider: {provider}")