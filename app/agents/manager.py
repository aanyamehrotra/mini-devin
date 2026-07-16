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
                review.feedback,
            )

        print(f"\n========== Attempt {i + 1} ==========")
        print("Generating code...")

        execution = execute_code(code)

        print("Execution Success:", execution.success)

        if not execution.success:
            print("Execution Error:")
            print(execution.stderr)

        review = review_code(
            plan,
            code,
            execution,
        )

        print("Reviewer:")
        print(review.feedback)

        attempts.append(
            {
                "attempt": i + 1,
                "code": code,
                "execution": execution,
                "review": review,
                "success": review.success,
            }
        )

        if review.success:
            print("SUCCESS")
            break

        print("Rewriting...")

    return {
        "plan": plan,
        "code": code,
        "execution": execution,
        "review": review,
        "attempts": attempts,
    }