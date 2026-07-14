from app.models.schemas import Plan
from app.services.llm.factory import get_llm
import json

from app.models.schemas import (
    Plan,
    CodeResponse,
)
from app.services.llm.factory import get_llm

def write_code(plan: Plan) -> CodeResponse:

    llm = get_llm()

    prompt = f"""
You are an expert Python software engineer.

Your task is to generate an entire software project.

Goal:
{plan.goal}

Features:
{chr(10).join("- " + feature for feature in plan.features)}

Files:
{chr(10).join("- " + file for file in plan.files)}

Implementation Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(plan.steps))}

Return ONLY valid JSON.

The JSON MUST exactly follow this schema:

{{
  "files": [
    {{
      "path": "main.py",
      "content": "print('Hello')"
    }}
  ]
}}
IMPORTANT

The generated program must run autonomously.

Do NOT use input().

If values are needed, assign realistic sample values directly in variables.

The program must execute successfully without requiring any user interaction.

Rules:

- Return ONLY JSON.
- No markdown.
- No triple backticks.
- No explanation.
- Every file listed above MUST appear exactly once.
- The content field must contain the complete file contents.
"""

    response = llm.generate(prompt).strip()

    if response.startswith("```"):
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()

    start = response.find("{")
    end = response.rfind("}") + 1
    response = response[start:end]

    data = json.loads(response)

    return CodeResponse(**data)

def rewrite_code(
    plan: Plan,
    previous_code: CodeResponse,
    review: str,
) -> CodeResponse:

    llm = get_llm()

    prompt = f"""
You are an expert Python software engineer.

The previous implementation failed review.

Project Goal:
{plan.goal}

Required Features:
{chr(10).join("- " + feature for feature in plan.features)}

Current Project:

{previous_code.model_dump_json(indent=2)}

Reviewer Feedback:

{review}

Return ONLY valid JSON.

Use the exact same schema:

{{
  "files": [
    {{
      "path": "main.py",
      "content": "..."
    }}
  ]
}}

IMPORTANT

The generated program must run autonomously.

Do NOT use input().

If values are needed, assign realistic sample values directly in variables.

The program must execute successfully without requiring any user interaction.

Rules:

- Return ONLY JSON.
- No markdown.
- No explanation.
- Keep every existing file unless the reviewer explicitly asks to remove it.
- Fix only the issues mentioned.
"""

    response = llm.generate(prompt).strip()

    if response.startswith("```"):
        response = response.replace("```json", "")
        response = response.replace("```", "")
        response = response.strip()

    start = response.find("{")
    end = response.rfind("}") + 1
    response = response[start:end]

    data = json.loads(response)

    return CodeResponse(**data)