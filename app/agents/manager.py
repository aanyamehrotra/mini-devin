from app.agents.planner import plan_task
from app.agents.coder import write_code, rewrite_code
from app.agents.reviewer import review_code
from app.executor.runner import execute_code


MAX_RETRIES = 3


def run_agent(user_prompt: str):
    plan = plan_task(user_prompt)

    attempts = []

    for i in range(MAX_RETRIES):

        if i == 0:
            code = write_code(plan)
        else:
            code = rewrite_code(
                plan,
                code,
                review
            )

        execution = execute_code(code)

        review = review_code(
            plan,
            code,
            execution
        )

        attempts.append({
            "attempt": i + 1,
            "code": code,
            "execution": execution,
            "review": review,
            "success": execution.success
        })

        if review == "SUCCESS":
            break

    return {
        "plan": plan,
        "code": code,
        "execution": execution,
        "review": review,
        "attempts": attempts
    }