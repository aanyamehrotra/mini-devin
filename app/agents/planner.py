from app.services.gemini_service import generate_response


def plan_task(user_request: str):
    prompt = f"""
You are the Planner Agent in an autonomous software engineering system.

Your ONLY responsibility is planning.

DO NOT write code.
DO NOT explain implementation details.
DO NOT generate functions or classes.

Given the user's request:

{user_request}

Return ONLY this structure:

Goal:
...

Features:
- ...
- ...
- ...

Files:
- ...
- ...

Technologies:
- ...

Implementation Steps:
1.
2.
3.
4.

Return plain text only.
"""

    return generate_response(prompt)