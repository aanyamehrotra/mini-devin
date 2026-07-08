from app.models.schemas import Plan
from app.services.gemini_service import generate_response

def write_code(plan: Plan) -> str:
    prompt = f"""
You are an expert Python software engineer.

Your job is to implement the project described below.

Goal:
{plan.goal}

Features:
{chr(10).join("- " + feature for feature in plan.features)}

Files:
{chr(10).join("- " + file for file in plan.files)}

Implementation Steps:
{chr(10).join(str(i+1)+". "+step for i, step in enumerate(plan.steps))}

Write complete, production-quality Python code.

Return ONLY the code.

Do not explain anything.

Do not wrap it inside markdown.
"""

    return generate_response(prompt).strip()