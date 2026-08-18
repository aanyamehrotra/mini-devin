import json

from app.models.schemas import (
    Plan,
    ExecutionResult,
    CodeResponse,
    ReviewResult,
)
from app.services.llm.factory import get_llm


def review_code(
    plan: Plan,
    code: CodeResponse,
    execution: ExecutionResult,
    user_request
) -> ReviewResult:

    llm = get_llm()

    prompt = f"""
You are the Reviewer Agent in an autonomous coding system.

Determine whether the generated project satisfies the user's request.

USER REQUEST:
{user_request}

PROJECT GOAL:
{plan.goal}

REQUIRED FEATURES:
{chr(10).join("- " + feature for feature in plan.features)}

GENERATED PROJECT:
{code.model_dump_json(indent=2)}

EXECUTION:
success={execution.success}
exit_code={execution.exit_code}
stdout={execution.stdout}
stderr={execution.stderr}
error_type={execution.error_type}

REVIEW RULES:
- Check the requested goal and every required feature.
- Do not invent problems or demand stylistic changes when the code is functionally correct.
- Execution failure does not automatically mean the code is wrong; distinguish code problems from environment problems.
- Multiple files do not all need to execute directly.
- Interactive input is never allowed.
- If the code is correct, return success=true and failure_source=null.
- If generated code is wrong, return success=false and failure_source="code".
- If dependencies are missing or incorrect, return success=false and failure_source="requirements".
- If the execution environment caused the failure, return success=false and failure_source="execution_environment".
- When unsuccessful, give the Fixer a concise, specific description of what must change.

Return ONLY valid JSON:

{{
    "success": true,
    "feedback": "Brief review result.",
    "failure_source": null
}}

failure_source must be exactly:
"code", "requirements", "execution_environment", or null.

No markdown. No explanation outside the JSON.
"""

    response = llm.generate(prompt).strip()

    data = json.loads(response)

    return ReviewResult(**data)