from app.memory.context import with_references
from app.models.schemas import Plan, CodeResponse
from app.services.llm.structured import generate_structured


def write_code(plan: Plan, user_request, context=None) -> CodeResponse:

    prompt = f"""
    You are the Coder Agent in an autonomous software engineering system.

    Generate the complete executable project described below.

    USER REQUEST:
    {user_request}

    PLAN:
    Goal: {plan.goal}

    Features:
    {chr(10).join("- " + feature for feature in plan.features)}

    Files:
    {chr(10).join("- " + file for file in plan.files)}

    Steps:
    {chr(10).join(f"{i+1}. {step}" for i, step in enumerate(plan.steps))}

    Return ONLY JSON in this exact format:

    {{
      "files": [
        {{
          "path": "main.py",
          "content": "..."
        }}
      ]
    }}

    CODING RULES:
    - Generate complete, executable code.
    - Always include main.py as the entry point.
    - Include every file listed in the plan.
    - Add additional files only when necessary.
    - Every file must appear exactly once.
    - The program must run autonomously.
    - Never use input() or wait for interactive stdin.
    - Use realistic sample values when values are unspecified.
    - Never install packages from inside Python code.
    - Put external Python dependencies in requirements.txt, one package per line.
    - Do not include standard-library modules in requirements.txt.
    - Do not create requirements.txt when no external packages are needed.
    - Preserve the user's exact requirements, strings, numbers, filenames, constraints, and expected outputs.

    Return JSON only. No markdown or explanation.
    """
    return generate_structured(with_references(prompt, context), CodeResponse, "coder")

def rewrite_code(
    plan: Plan,
    previous_code: CodeResponse,
    review: str,
    context=None,
) -> CodeResponse:


    prompt = f"""
You are the Fixer Agent in an autonomous software engineering system.

The generated project failed review. Fix the implementation while preserving the user's requirements.

PROJECT GOAL:
{plan.goal}

REQUIRED FEATURES:
{chr(10).join("- " + feature for feature in plan.features)}

CURRENT PROJECT:
{previous_code.model_dump_json(indent=2)}

REVIEWER FEEDBACK:
{review}

Return ONLY JSON in this exact format:

{{
  "files": [
    {{
      "path": "main.py",
      "content": "..."
    }}
  ]
}}

FIXING RULES:
- Fix the issues identified by the reviewer.
- Preserve code that is already correct.
- Keep existing files unless they must be changed.
- Add files only when necessary.
- Keep main.py as the entry point.
- Preserve the user's exact requirements.
- The program must run autonomously.
- Never use input() or wait for interactive stdin.
- Use realistic sample values when needed.
- Never install packages inside Python code.
- Include external dependencies in requirements.txt.
- Do not include standard-library modules in requirements.txt.

Return JSON only. No markdown or explanation.
"""

    return generate_structured(with_references(prompt, context), CodeResponse, "rewrite")
