from app.services.gemini_service import generate_response

def generate_code(plan:str):
    prompt=  f"""
You are the Coder Agent in an autonomous software engineering system.

Your ONLY responsibility is writing code.

You will receive a project plan.

Plan:

{plan}

Rules:

- Generate working code.
- Do not explain the solution.
- Do not include markdown.
- Do not wrap code inside ``` blocks.
- Return only the source code.
"""

    return generate_response(prompt)