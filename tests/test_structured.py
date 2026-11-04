import json
import unittest
from unittest.mock import Mock, patch

from app.models.schemas import CodeResponse, ReviewResult, ChatRequest
from app.services.llm.structured import generate_structured, AgentResponseError


class StructuredTests(unittest.TestCase):
    def generate(self, response, schema=CodeResponse):
        with patch('app.services.llm.structured.get_llm', return_value=Mock(generate=Mock(return_value=response))):
            return generate_structured('task', schema, 'coder')

    def test_preserves_backticks_and_braces_inside_code(self):
        content = 'print("```json {example} ```")'
        payload = json.dumps({'files': [{'path': 'main.py', 'content': content}]})
        for text in [payload, '```json\n'+payload+'\n```', '```\n'+payload+'\n```']:
            with self.subTest(text=text):
                self.assertEqual(self.generate(text).files[0].content, content)

    def test_invalid_output_classified(self):
        for response, kind in [(None, 'empty_response'), (' ', 'empty_response'),
                               ('explanation {"files": []}', 'invalid_json'),
                               ('{} {}', 'invalid_json'), ('[]', 'invalid_schema'),
                               ('{}', 'invalid_schema'), ('{"files": "bad"}', 'invalid_schema')]:
            with self.subTest(response=response), self.assertRaises(AgentResponseError) as raised:
                self.generate(response)
            self.assertEqual(raised.exception.kind, kind)

    def test_boolean_strings_are_not_coerced(self):
        with self.assertRaises(AgentResponseError):
            self.generate('{"success":"false","feedback":"failed"}', ReviewResult)

    def test_provider_initialization_and_generation_failures(self):
        for provider in [Mock(side_effect=ValueError('secret-token')),
                         Mock(return_value=Mock(generate=Mock(side_effect=RuntimeError('secret-token'))))]:
            with patch('app.services.llm.structured.get_llm', provider), self.assertRaises(AgentResponseError) as raised:
                generate_structured('task', CodeResponse, 'planner')
            self.assertEqual(raised.exception.kind, 'provider_failure')
            self.assertNotIn('secret-token', str(raised.exception))

    def test_route_returns_safe_gateway_error(self):
        from fastapi import HTTPException
        from app.routes.chat import chat
        with patch('app.routes.chat.run_agent', side_effect=AgentResponseError('reviewer', 'invalid_json')):
            with self.assertRaises(HTTPException) as raised:
                chat(ChatRequest(prompt='hello'))
        self.assertEqual(raised.exception.status_code, 502)
        self.assertEqual(raised.exception.detail, {'error': 'invalid_json', 'stage': 'reviewer'})

    def test_planner_failure_stops_before_execution(self):
        from app.agents.manager import run_agent
        with patch('app.services.llm.structured.get_llm', return_value=Mock(generate=Mock(return_value='bad'))), patch('app.agents.manager.execute_code') as execute:
            with self.assertRaises(AgentResponseError):
                run_agent('hello')
            execute.assert_not_called()
