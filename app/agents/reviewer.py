from app.models.schemas import Plan, ExecutionResult, CodeResponse
from app.services.llm.factory import get_llm


def review_code(
    plan: Plan,
    code: CodeResponse,
    execution: ExecutionResult,
) -> str:
    
    llm=get_llm()

    prompt = f"""
You are the Reviewer Agent in an autonomous coding system.

Your job is to evaluate whether the generated code correctly satisfies the requested plan.

Project Goal:
{plan.goal}

Required Features:
{chr(10).join("- " + feature for feature in plan.features)}

Generated Project:

{code.model_dump_json(indent=2)}

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

    return llm.generate(prompt).strip()