import json

from app.models.schemas import Plan, CodeResponse
from app.services.llm.factory import get_llm


def write_code(plan: Plan) -> CodeResponse:
    llm = get_llm()

    prompt = f"""
You are an expert Python software engineer.

Your task is to generate a complete, executable software project.

Goal:
{plan.goal}

Features:
{chr(10).join("- " + feature for feature in plan.features)}

Suggested Files:
{chr(10).join("- " + file for file in plan.files)}

Implementation Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(plan.steps))}

Return ONLY valid JSON.

The JSON MUST exactly follow this schema:

{{
  "files": [
    {{
      "path": "main.py",
      "content": "..."
    }},
    {{
      "path": "requirements.txt",
      "content": "flask\\nrequests"
    }}
  ]
}}

Each object represents one file in the project.

Dependency Rules:

- If the project uses any external Python package (Flask, FastAPI, requests, pandas, numpy, matplotlib, sqlalchemy, etc.), you MUST generate a requirements.txt file.
- requirements.txt must contain one package per line.
- Do NOT include Python standard library modules.
- If only the Python standard library is used, do NOT generate requirements.txt.

Project Rules:

- Always generate main.py as the project entry point.
- Every file suggested above MUST appear.
- You may generate additional files if needed to make the project complete.
- Examples include requirements.txt, utils.py, models.py, config.py and README.md.
- Every generated file must appear exactly once.

Execution Rules:

- The generated program must run autonomously.
- Do NOT use input().
- If values are needed, assign realistic sample values directly.
- Do NOT install packages inside Python code.
- Assume dependencies will be installed from requirements.txt.

Rules:

- Return ONLY valid JSON.
- No markdown.
- No triple backticks.
- No explanation.
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

Use this schema:

{{
  "files": [
    {{
      "path": "main.py",
      "content": "..."
    }}
  ]
}}

Execution Rules:

- The program must run autonomously.
- Do NOT use input().
- Assign sample values wherever needed.
- Do NOT install packages inside Python code.
- If external packages are required, include or update requirements.txt.

Project Rules:

- Keep every existing file unless the reviewer explicitly requests otherwise.
- Fix only the issues mentioned by the reviewer.
- Preserve files that are already correct.
- You may add new files if required to make the project executable.
- Always keep main.py as the entry point.

Rules:

- Return ONLY JSON.
- No markdown.
- No explanation.
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