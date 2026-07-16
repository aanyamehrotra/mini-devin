import json

from app.models.schemas import Plan
from app.services.llm.factory import get_llm


def plan_task(user_request: str) -> Plan:

    llm = get_llm()

    prompt = f"""
    You are the Planner Agent in an autonomous software engineering system.

    Your ONLY responsibility is planning.

    DO NOT write code.
    DO NOT explain implementation details.

    Given this request:

    {user_request}

    Return ONLY valid JSON.

    The JSON must exactly follow this schema:

    {{
        "goal": "short project goal",
        "features": [
            "feature 1",
            "feature 2"
        ],
        "files": [
            "main.py"
        ],
        "technologies": [
            "Python"
        ],
        "steps": [
            "step 1",
            "step 2",
            "step 3"
        ]
    }}
    CRITICAL RULES:
    - Do not invent features or requirements that the user did not explicitly request.
    - The generated program must be suitable for autonomous execution.
    - Do not plan interactive terminal input using input().
    - If values are needed and the user did not specify them, use realistic sample values.
    - Only include features directly required to satisfy the user's request.
        Return ONLY the JSON.
    IMPORTANT:
    Preserve all exact user-provided details in the plan, including literal strings,
    numbers, filenames, technologies, constraints, and expected outputs.

    Never replace a specific requirement with a generic description.

    Example:
    User: Print "Hello Mini Devin"
    Correct feature: Print exactly "Hello Mini Devin"
    Incorrect feature: Print a greeting message
    No markdown.
    No explanation.
    No backticks.
    """

    response = llm.generate(prompt).strip()

    if response.startswith("```"):
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()

    start = response.find("{")
    end = response.rfind("}") + 1

    response = response[start:end]

    data = json.loads(response)

    return Plan(**data)