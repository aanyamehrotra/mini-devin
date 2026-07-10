from app.models.schemas import Plan, ExecutionResult
from app.services.gemini_service import generate_response


def review_code(
    plan: Plan,
    code: str,
    execution: ExecutionResult,
) -> str:

    prompt = f"""
You are the Reviewer Agent in an autonomous coding system.

Your job is to evaluate whether the generated code correctly satisfies the requested plan.

Project Goal:
{plan.goal}

Required Features:
{chr(10).join("- " + feature for feature in plan.features)}

Generated Code:

{code}

Execution Result

Success:
{execution.success}

Exit Code:
{execution.exit_code}

Stdout:
{execution.stdout}

Stderr:
{execution.stderr}

If the code is correct and execution succeeded,
respond with ONLY:

SUCCESS

Otherwise,
explain what is wrong and describe exactly what the Coder Agent should fix.

Do NOT rewrite the entire solution.
Do NOT generate code.
Return only the review.
"""

    return generate_response(prompt).strip()