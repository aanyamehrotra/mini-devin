import json
from app.models.schemas import Plan
from app.services.gemini_service import generate_response


def plan_task(user_request: str) -> Plan :
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

    Return ONLY the JSON.

    No markdown.
    No explanation.
    No backticks.
    """
    response = generate_response(prompt)
    response = response.strip()

    if response.startswith("```"):
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()
    data = json.loads(response)

    return Plan(**data)