import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import create_app
from app.models.schemas import ExecutionResult

class ProjectExecutionTests(unittest.TestCase):
    def test_anonymous_cannot_bypass_demo_quota_with_manual_execution(self):
        with patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':'private-token'}),patch('app.routes.projects.execute_code') as execute,TestClient(create_app('/absent')) as client:
            self.assertEqual(client.post('/api/projects/execute',json={'files':[{'path':'main.py','content':'print(1)'}]}).status_code,401)
            execute.assert_not_called()
    def test_owner_manual_run_is_marked_without_ai_review_or_history_write(self):
        execution=ExecutionResult(success=True,stdout='42\n',stderr='',exit_code=0,execution_time=.1)
        with patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':'private-token'}),patch('app.routes.projects.execute_code',return_value=execution) as execute,patch('app.storage.runs.save_run') as save,TestClient(create_app('/absent')) as client:
            response=client.post('/api/projects/execute',headers={'Authorization':'Bearer private-token'},json={'files':[{'path':'main.py','content':'print(42)'}]})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['review']['mode'],'not_requested')
        self.assertEqual(response.json()['execution']['stdout'],'42\n')
        execute.assert_called_once();save.assert_not_called()
