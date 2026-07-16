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

AUTONOMOUS EXECUTION RULES:
- The generated project must run without interactive terminal input.
- Never require the use of input().
- Do not mark a solution incorrect merely because it uses sample values instead of input().
- Do not suggest adding input() as a fix.
- Evaluate the implementation against the user's actual request and the execution environment.
- If the plan incorrectly introduces interactive input that the user did not request, do not require the implementation to follow that incorrect requirement.

REVIEW RULES:

1. Judge the generated project based on actual correctness and the user's requirements.
2. If execution succeeded with the expected output, do not invent problems without concrete evidence.
3. Valid Python module imports include:
   - import module_name
   - from module_name import item
   A local file named module_name.py can be imported using "import module_name".
4. Do not require stylistic changes when the existing implementation is functionally correct.
5. If the project fully satisfies the request, respond with exactly:SUCCESS
6. If there is any actual issue, explain the issue and required fix, and DO NOT include the word SUCCESS anywhere in the response.
- Evaluate whether the code satisfies the user's request, not merely whether execution.success is true.
- An execution failure does not automatically mean the code is incorrect.
- Consider whether the observed execution result is expected for the requested behavior.
- For example, if the user explicitly requests an infinite loop and execution ends because of the environment's timeout limit, the code may still fully satisfy the request.
- Never request a rewrite when you explicitly determine that no code changes are necessary.

Do NOT rewrite the entire solution.
Do NOT generate code.
Return only the review.
"""

    return llm.generate(prompt).strip()