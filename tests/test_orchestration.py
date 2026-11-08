import unittest
from contextlib import ExitStack
from unittest.mock import patch

from app.agents import manager
from app.models.schemas import Plan, CodeResponse, GeneratedFile, ExecutionResult, ReviewResult
from app.services.llm.structured import AgentResponseError


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.plan = Plan(goal='print hello', features=['print hello'], files=['main.py'],
                         technologies=['Python'], steps=['print hello'])
        self.code = CodeResponse(files=[GeneratedFile(path='main.py', content='print("hello")')])
        self.good = ExecutionResult(success=True, stdout='hello', stderr='', exit_code=0, execution_time=0.1)
        self.bad = ExecutionResult(success=False, stdout='', stderr='NameError', exit_code=1,
                                   execution_time=0.1, error_type='NameError')
        self.approved = ReviewResult(success=True, feedback='matches request')
        self.rejected = ReviewResult(success=False, feedback='fix the name', failure_source='code')
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.mocks = {}
        for name, value in [('plan_task', self.plan), ('write_code', self.code),
                            ('rewrite_code', self.code), ('execute_code', self.good),
                            ('review_code', self.approved)]:
            self.mocks[name] = self.stack.enter_context(patch.object(manager, name, return_value=value))

    def test_first_attempt_success_preserves_response_shape(self):
        result = manager.run_agent('hello')
        self.assertEqual(set(result), {'plan', 'code', 'execution', 'review', 'attempts'})
        self.assertEqual(len(result['attempts']), 1)
        self.assertTrue(result['attempts'][0]['success'])
        self.mocks['rewrite_code'].assert_not_called()

    def test_failed_attempt_rewrites_with_feedback_and_retains_history(self):
        self.mocks['execute_code'].side_effect = [self.bad, self.good]
        self.mocks['review_code'].side_effect = [self.rejected, self.approved]
        result = manager.run_agent('hello')
        self.assertEqual([a['success'] for a in result['attempts']], [False, True])
        self.assertEqual(result['attempts'][0]['execution'].stderr, 'NameError')
        self.mocks['rewrite_code'].assert_called_once_with(self.plan, self.code, 'fix the name')

    def test_retry_limit_is_total_attempts(self):
        self.mocks['execute_code'].return_value = self.bad
        self.mocks['review_code'].return_value = self.rejected
        result = manager.run_agent('hello')
        self.assertEqual(len(result['attempts']), manager.MAX_RETRIES)
        self.assertEqual(self.mocks['rewrite_code'].call_count, manager.MAX_RETRIES - 1)

    def test_environment_failure_skips_reviewer_and_rewrite(self):
        self.mocks['execute_code'].return_value = self.bad.model_copy(
            update={'error_type': 'ExecutionEnvironment', 'stderr': 'Docker unavailable'})
        result = manager.run_agent('hello')
        self.assertFalse(result['review'].success)
        self.assertEqual(len(result['attempts']), 1)
        self.mocks['review_code'].assert_not_called()
        self.mocks['rewrite_code'].assert_not_called()

    def test_reviewer_cannot_approve_failed_execution(self):
        self.mocks['execute_code'].return_value = self.bad
        result = manager.run_agent('hello')
        self.assertEqual(len(result['attempts']), manager.MAX_RETRIES)
        self.assertFalse(result['review'].success)
        self.assertFalse(any(a['success'] for a in result['attempts']))

    def test_separate_requests_do_not_share_history(self):
        first = manager.run_agent('one')
        second = manager.run_agent('two')
        self.assertEqual(len(first['attempts']), 1)
        self.assertEqual(len(second['attempts']), 1)
        self.assertIsNot(first['attempts'], second['attempts'])

    def test_provider_error_propagates_without_execution(self):
        self.mocks['plan_task'].side_effect = AgentResponseError('planner', 'provider_failure')
        with self.assertRaises(AgentResponseError):
            manager.run_agent('hello')
        self.mocks['execute_code'].assert_not_called()

    def test_invalid_attempt_limit(self):
        for limit in [0, -1, True, 1.5]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                manager.build_graph(limit)

    def test_graph_stream_emits_ordered_stage_updates(self):
        events = list(manager.build_graph().stream({'user_prompt': 'hello', 'attempts': []}, stream_mode='updates'))
        self.assertEqual([next(iter(event)) for event in events], ['plan', 'generate', 'execute', 'review'])

    def test_custom_single_attempt_limit(self):
        self.mocks['execute_code'].return_value = self.bad
        self.mocks['review_code'].return_value = self.rejected
        result = manager.build_graph(1).invoke({'user_prompt': 'hello', 'attempts': []})
        self.assertEqual(len(result['attempts']), 1)
        self.mocks['rewrite_code'].assert_not_called()

    def test_http_request_runs_graph_and_serializes_history(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            response = client.post('/chat', json={'prompt': 'hello'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['attempts'][0]['success'])
        self.assertEqual(response.json()['code']['files'][0]['path'], 'main.py')

    def test_http_request_maps_graph_provider_failure(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.mocks['plan_task'].side_effect = AgentResponseError('planner', 'provider_failure')
        with TestClient(app) as client:
            response = client.post('/chat', json={'prompt': 'hello'})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['detail'], {'error': 'provider_failure', 'stage': 'planner'})

    def test_http_invalid_request_stops_before_graph(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            response = client.post('/chat', json={})
        self.assertEqual(response.status_code, 422)
        self.mocks['plan_task'].assert_not_called()
