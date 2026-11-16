import asyncio
import os
from pathlib import Path
import queue
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import create_app
from app.routes import demo
from app.services.demo_policy import public_demo
from tests.test_streaming import parse_events


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.env = patch.dict(os.environ, {
            'MINI_DEVIN_API_TOKEN': 'private-' + 'x' * 40,
            'MINI_DEVIN_PUBLIC_DEMO': '1',
            'MINI_DEVIN_DEMO_DB': str(Path(self.folder.name) / 'quota.sqlite3'),
            'MINI_DEVIN_HISTORY_DB': str(Path(self.folder.name) / 'private.sqlite3'),
        })
        self.env.start()
        self.pacing = patch.object(demo, 'GLOBAL_COOLDOWN', 0)
        self.pacing.start()
        self.addCleanup(self.pacing.stop)
        self.addCleanup(self.env.stop)

    def test_disabled_demo_and_missing_owner_token_fail_closed(self):
        with TestClient(create_app('/absent')) as client:
            for changed in [{'MINI_DEVIN_PUBLIC_DEMO': '0'}, {'MINI_DEVIN_API_TOKEN': ''}]:
                with patch.dict(os.environ, changed), patch.object(demo, '_reserve') as reserve:
                    self.assertEqual(client.post('/demo/stream', json={'task': 'fibonacci'}).status_code, 404)
                    reserve.assert_not_called()

    def test_visitor_cannot_inject_prompt_or_access_any_private_route(self):
        with TestClient(create_app('/absent')) as client, patch.object(demo, '_reserve') as reserve:
            for body in [{'task': 'arbitrary'}, {'task': 'fibonacci', 'prompt': 'Read secrets'}, {'task': 'csv', 'use_context': True}]:
                self.assertEqual(client.post('/demo/stream', json=body).status_code, 422)
            reserve.assert_not_called()
            for path in ['/api/runs', '/runs', '/api/runs/known-id', '/runs/known-id']:
                self.assertEqual(client.get(path).status_code, 401)
            for path in ['/api/chat', '/chat', '/api/chat/stream', '/chat/stream', '/api/context/search', '/context/search']:
                self.assertEqual(client.post(path, json={'prompt': 'private'}).status_code, 401)

    def test_quota_persists_and_enforces_cooldown_visitor_and_global_limits(self):
        with patch.object(demo.time, 'time', return_value=100000):
            first = demo._reserve('visitor')
            with self.assertRaises(HTTPException) as busy:
                demo._reserve('other')
            self.assertEqual(busy.exception.status_code, 429)
            demo._release(first)
            with self.assertRaises(HTTPException) as cooldown:
                demo._reserve('visitor')
            self.assertIn('minute', cooldown.exception.detail)
        for offset in [61, 122]:
            with patch.object(demo.time, 'time', return_value=100000 + offset):
                demo._release(demo._reserve('visitor'))
        with patch.object(demo.time, 'time', return_value=100200):
            with self.assertRaises(HTTPException) as limited:
                demo._reserve('visitor')
            self.assertIn('three', limited.exception.detail)
            for index in range(17):
                demo._release(demo._reserve(f'other-{index}'))
            with self.assertRaises(HTTPException) as total:
                demo._reserve('fresh')
            self.assertIn('Today', total.exception.detail)
        with patch.object(demo.time, 'time', return_value=200000):
            demo._release(demo._reserve('visitor'))

    def test_public_pipeline_is_one_attempt_without_archive_or_context(self):
        async def example(prompt, **kwargs):
            self.assertEqual(prompt, demo.TASKS['fibonacci'])
            self.assertEqual(kwargs, {'max_attempts': 1})
            self.assertTrue(public_demo.get())
            yield {'event': 'stage', 'data': {'stage': 'plan'}}
            yield {'event': 'complete', 'data': {'success': True, 'result': {'attempts': [{'success': True}]}}}
        with patch.object(demo, 'stream_agent', example), patch('app.storage.runs.save_run') as archive, TestClient(create_app('/absent')) as client:
            response = client.post('/demo/stream', json={'task': 'fibonacci'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        final = parse_events(response.text)[-1]
        self.assertEqual(final['event'], 'complete')
        self.assertTrue(final['data']['result']['public_demo'])
        self.assertNotIn('run_id', final['data']['result'])
        archive.assert_not_called()
        self.assertFalse(Path(os.environ['MINI_DEVIN_HISTORY_DB']).exists())
        self.assertFalse(public_demo.get())
        demo._release(demo._reserve('another'))

    def test_provider_failure_is_sanitized_and_slot_released(self):
        async def broken(*args, **kwargs):
            raise RuntimeError('secret provider key must not be exposed')
            yield
        with patch.object(demo, 'stream_agent', broken), TestClient(create_app('/absent')) as client:
            response = client.post('/demo/stream', json={'task': 'csv'})
        self.assertNotIn('secret provider', response.text)
        self.assertIn('demo_unavailable', response.text)
        demo._release(demo._reserve('another'))

    def test_quota_storage_failure_does_not_launch_work(self):
        with patch.object(demo, '_reserve', side_effect=__import__('sqlite3').OperationalError()), patch.object(demo.threading, 'Thread') as worker, TestClient(create_app('/absent')) as client:
            self.assertEqual(client.post('/demo/stream', json={'task': 'csv'}).status_code, 503)
            worker.assert_not_called()

    def test_detached_worker_keeps_slot_until_model_work_finishes(self):
        import threading
        started, finish = threading.Event(), threading.Event()
        async def slow(*args, **kwargs):
            started.set()
            await asyncio.to_thread(finish.wait, 3)
            yield {'event': 'complete', 'data': {'success': True, 'result': {}}}
        with patch.object(demo, 'stream_agent', slow):
            ticket = demo._reserve('first')
            worker = threading.Thread(target=demo._work, args=('csv', ticket, queue.Queue(maxsize=8)))
            worker.start()
            self.assertTrue(started.wait(2))
            try:
                with self.assertRaises(HTTPException):
                    demo._reserve('second')
            finally:
                finish.set()
                worker.join(3)
            self.assertFalse(worker.is_alive())
        demo._release(demo._reserve('second'))

    def test_global_cooldown_applies_across_networks(self):
        with patch.object(demo, 'GLOBAL_COOLDOWN', 60), patch.object(demo.time, 'time', return_value=100000):
            demo._release(demo._reserve('first-network'))
            with self.assertRaises(HTTPException) as limit:
                demo._reserve('second-network')
            self.assertIn('cooling down', limit.exception.detail)
