"""Shared boundary for provider failures and structured agent responses."""

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.services.llm.factory import get_llm

T = TypeVar('T', bound=BaseModel)


class AgentResponseError(RuntimeError):
    def __init__(self, stage: str, kind: str):
        self.stage = stage
        self.kind = kind
        super().__init__(f'{stage}: {kind}')


def generate_structured(prompt: str, schema: type[T], stage: str) -> T:
    try:
        response = get_llm().generate(prompt)
    except Exception as error:
        # Keep provider details out of public errors (they can contain secrets).
        raise AgentResponseError(stage, 'provider_failure') from error
    if not isinstance(response, str) or not response.strip():
        raise AgentResponseError(stage, 'empty_response')
    response = response.strip()
    lines = response.splitlines()
    if lines[0].lower() in ('```json', '```') and len(lines) >= 3 and lines[-1] == '```':
        response = '\n'.join(lines[1:-1])
    try:
        data = json.loads(response)
    except ValueError as error:
        raise AgentResponseError(stage, 'invalid_json') from error
    if not isinstance(data, dict):
        raise AgentResponseError(stage, 'invalid_schema')
    try:
        return schema.model_validate(data, strict=True)
    except ValidationError as error:
        raise AgentResponseError(stage, 'invalid_schema') from error
