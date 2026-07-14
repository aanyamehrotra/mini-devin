from app.services.llm.factory import get_llm


llm = get_llm()

response = llm.generate("Say Hello from Groq.")

print(response)