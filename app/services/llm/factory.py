from app.config import ACTIVE_LLM


def get_llm():

    provider = ACTIVE_LLM.strip().lower()

    if provider == "groq":
        from app.services.llm.groq import GroqLLM
        return GroqLLM()

    elif provider == "gemini":
        from app.services.llm.gemini import GeminiLLM
        return GeminiLLM()

    elif provider == "ollama":
        from app.services.llm.ollama import OllamaLLM
        return OllamaLLM()

    raise ValueError(f"Unsupported provider: {provider}")