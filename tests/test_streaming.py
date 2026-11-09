import asyncio
import json

from tests import test_orchestration
from app.agents import manager
from app.services.llm.structured import AgentResponseError
import unittest


def parse_events(text):
    events = []
    for block in text.strip().split('\n\n'):
        fields = dict(line.split(': ', 1) for line in block.splitlines())
        fields['data'] = json.loads(fields['data'])
        events.append(fields)
    return events


class StreamingTests(unittest.TestCase):
    setUp = test_orchestration.OrchestrationTests.setUp

    def request(self, payload=None):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            return client.post('/chat/stream', json=payload or {'prompt': 'hello'})

    def test_http_event_order_and_final_history(self):
        response = self.request()
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/event-stream', response.headers['content-type'])
        self.assertEqual(response.headers['cache-control'], 'no-cache')
        events = parse_events(response.text)
        self.assertEqual([e['event'] for e in events], ['started'] + ['stage']*4 + ['complete'])
        self.assertEqual([e['id'] for e in events], [str(i) for i in range(1, 7)])
        self.assertEqual([e['data']['stage'] for e in events[1:-1]], ['plan', 'generate', 'execute', 'review'])
        self.assertTrue(events[-1]['data']['success'])
        self.assertEqual(events[-1]['data']['result']['code']['files'][0]['path'], 'main.py')

    def test_retry_events_include_attempt_numbers(self):
        self.mocks['execute_code'].side_effect = [self.bad, self.good]
        self.mocks['review_code'].side_effect = [self.rejected, self.approved]
        events = parse_events(self.request().text)
        reviews = [e['data']['attempt'] for e in events if e['event'] == 'stage' and e['data']['stage'] == 'review']
        self.assertEqual(reviews, [1, 2])
        self.assertEqual(len(events[-1]['data']['result']['attempts']), 2)

    def test_provider_error_is_terminal_event(self):
        self.mocks['plan_task'].side_effect = AgentResponseError('planner', 'provider_failure')
        events = parse_events(self.request().text)
        self.assertEqual([e['event'] for e in events], ['started', 'error'])
        self.assertEqual(events[-1]['data'], {'error': 'provider_failure', 'stage': 'planner'})

    def test_unexpected_error_does_not_expose_exception(self):
        self.mocks['plan_task'].side_effect = RuntimeError('secret-token')
        response = self.request()
        self.assertNotIn('secret-token', response.text)
        self.assertEqual(parse_events(response.text)[-1]['data'], {'error': 'internal_error'})

    def test_environment_failure_completes_with_false_status(self):
        self.mocks['execute_code'].return_value = self.bad.model_copy(update={'error_type': 'ExecutionEnvironment'})
        events = parse_events(self.request().text)
        self.assertEqual(events[-1]['event'], 'complete')
        self.assertFalse(events[-1]['data']['success'])
        self.mocks['rewrite_code'].assert_not_called()

    def test_invalid_body_returns_http_422_before_streaming(self):
        response = self.request({'other': 'missing prompt'})
        self.assertEqual(response.status_code, 422)
        self.mocks['plan_task'].assert_not_called()

    def test_cancel_between_stages_does_not_generate_code(self):
        async def collect():
            checks = 0
            async def cancelled():
                nonlocal checks
                checks += 1
                return checks > 1
            return [event async for event in manager.stream_agent('hello', cancelled=cancelled)]
        events = asyncio.run(collect())
        self.assertEqual([e['event'] for e in events], ['stage', 'cancelled'])
        self.mocks['write_code'].assert_not_called()
        self.mocks['execute_code'].assert_not_called()
