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
) -> ReviewResult:

    llm = get_llm()

    prompt = f"""
You are the Reviewer Agent in an autonomous coding system.

Your job is to determine whether the generated project correctly satisfies
the requested plan.

PROJECT GOAL:
{plan.goal}

REQUIRED FEATURES:
{chr(10).join("- " + feature for feature in plan.features)}

GENERATED PROJECT:
{code.model_dump_json(indent=2)}

EXECUTION RESULT:

Success:
{execution.success}

Exit Code:
{execution.exit_code}

Stdout:
{execution.stdout}

Stderr:
{execution.stderr}

Error Type:
{execution.error_type}


REVIEW RULES:

1. Evaluate whether the generated project actually satisfies the requested
   goal and required features.

2. Execution failure does NOT automatically mean the generated code is wrong.

3. Consider whether the observed execution behavior is expected for the
   requested task.

   Example:
   If the requested task is to create an infinite loop and execution stops
   because of the environment timeout, the code may still be correct.

4. If you determine that NO CODE CHANGES are necessary:
   - success must be true
   - failure_source must be null

5. If code changes ARE necessary:
   - success must be false
   - explain the exact required fix in feedback

6. Do not invent problems without concrete evidence.

7. Do not require stylistic changes when the implementation is functionally
   correct.

8. Valid Python imports include:
   - import module_name
   - from module_name import item

9. Multiple generated files do NOT all need to execute during a single run
   unless the requested behavior explicitly requires that.

10. The generated project must run without interactive terminal input.
    Never require or suggest input().

11. If execution failure is caused by the execution environment rather than
    incorrect generated code, set failure_source to "execution_environment".

12. If the problem is caused by generated code, set failure_source to "code".

13. If the problem is caused by missing or incorrect dependencies, set
    failure_source to "requirements".


RETURN FORMAT:

Return ONLY valid JSON matching exactly this structure:

{{
    "success": true,
    "feedback": "Brief explanation of the review result.",
    "failure_source": null
}}

failure_source must be exactly one of:

"code"
"execution_environment"
"requirements"
null

Do not include markdown.
Do not include code fences.
Do not include any text before or after the JSON.
"""

    response = llm.generate(prompt).strip()

    data = json.loads(response)

    return ReviewResult(**data)