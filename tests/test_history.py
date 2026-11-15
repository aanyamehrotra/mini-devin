import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app.storage.runs import save_run, list_runs, get_run
from tests import test_orchestration


class HistoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.db=str(Path(self.temp.name)/'private/runs.sqlite3')
        self.env=patch.dict(os.environ,{'MINI_DEVIN_HISTORY_DB':self.db});self.env.start();self.addCleanup(self.env.stop)
        self.result={'plan':{'goal':'example'},'attempts':[{'success':True}]}

    def test_persists_across_connections_and_returns_private_permissions(self):
        identifier=save_run('hello',self.result)
        self.assertEqual(get_run(identifier)['prompt'],'hello')
        self.assertEqual(get_run(identifier)['result']['run_id'],identifier)
        self.assertEqual(list_runs()[0]['id'],identifier)
        self.assertEqual(Path(self.db).stat().st_mode & 0o777,0o600)

    def test_retention_and_size_limits(self):
        with patch('app.storage.runs.MAX_RUNS',2):
            first=save_run('one',self.result)
            save_run('two',self.result);save_run('three',self.result)
        self.assertIsNone(get_run(first))
        self.assertEqual(len(list_runs()),2)
        with patch('app.storage.runs.MAX_RESULT_BYTES',1),self.assertRaises(ValueError):save_run('too big',self.result)

    def test_unknown_identifier_does_not_execute_sql(self):
        self.assertIsNone(get_run("' OR 1=1 --"))


class HistoryApiTests(unittest.TestCase):
    def setUp(self):
        test_orchestration.OrchestrationTests.setUp(self)
        folder=self.stack.enter_context(tempfile.TemporaryDirectory())
        self.stack.enter_context(patch.dict(os.environ,{'MINI_DEVIN_HISTORY_DB':str(Path(folder)/'runs.sqlite3'),'MINI_DEVIN_API_TOKEN':''}))

    def test_sync_result_can_be_loaded_after_request(self):
        from fastapi.testclient import TestClient
        from app.main import create_app
        with TestClient(create_app('/absent')) as client:
            result=client.post('/api/chat',json={'prompt':'hello'}).json()
            saved=client.get('/api/runs/'+result['run_id']).json()
            self.assertEqual(saved['result']['code'],result['code'])
            self.assertEqual(client.get('/api/runs').json()['runs'][0]['id'],result['run_id'])
            self.assertEqual(client.get('/api/runs/not-a-uuid').status_code,404)

    def test_stream_result_is_archived(self):
        from fastapi.testclient import TestClient
        from app.main import create_app
        from tests.test_streaming import parse_events
        with TestClient(create_app('/absent')) as client:
            events=parse_events(client.post('/api/chat/stream',json={'prompt':'hello'}).text)
            identifier=events[-1]['data']['result']['run_id']
            self.assertEqual(client.get('/api/runs/'+identifier).status_code,200)

    def test_history_is_protected_by_workspace_token(self):
        from fastapi.testclient import TestClient
        from app.main import create_app
        with patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':'fixture'}),TestClient(create_app('/absent')) as client:
            for path in ['/runs','/runs/'+'0'*32,'/api/runs']:
                self.assertEqual(client.get(path).status_code,401)

    def test_storage_failure_preserves_generated_result(self):
        from app.routes.chat import archive_result
        with patch('app.routes.chat.save_run',side_effect=OSError()):
            result=archive_result('hello',{'code':{'files':[]}})
        self.assertFalse(result['history_saved'])
        self.assertIn('code',result)
