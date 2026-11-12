from app.memory.context import with_references
from app.models.schemas import Plan
from app.services.llm.structured import generate_structured


def plan_task(user_request: str, context=None) -> Plan:


    prompt = f"""
    You are the Planner Agent in an autonomous coding system.

    Convert the user's request into a minimal implementation plan.

    USER REQUEST:
    {user_request}

    Return ONLY valid JSON matching this exact structure:

    {{
        "goal": "short project goal",
        "features": ["feature 1", "feature 2"],
        "files": ["main.py"],
        "technologies": ["Python"],
        "steps": ["step 1", "step 2", "step 3"]
    }}

    Rules:
    - Plan only; never write code.
    - Include only requirements explicitly requested by the user.
    - Preserve exact user-provided strings, numbers, filenames, technologies, constraints, and expected outputs.
    - Do not invent features.
    - Do not plan interactive input using input().
    - If unspecified values are required, use realistic sample values.
    - Keep the plan concise.
    - Return JSON only. No markdown or explanation.

    Example:
    User: Print "Hello Mini Devin"
    Correct: "Print exactly \\"Hello Mini Devin\\""
    Incorrect: "Print a greeting message"
    """

    return generate_structured(with_references(prompt, context), Plan, "planner")
