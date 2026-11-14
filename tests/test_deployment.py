from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import create_app
from app.services.readiness import readiness
from app.tools.preflight import main as preflight
from tests import test_orchestration


class ReadinessTests(unittest.TestCase):
    def test_configured_provider_and_live_engine(self):
        with patch('app.services.readiness.config.ACTIVE_LLM','groq'),patch('app.services.readiness.config.GROQ_API_KEY','fixture'),patch('app.services.readiness.subprocess.run',return_value=subprocess.CompletedProcess([],0,'version','')):
            result=readiness()
        self.assertTrue(result['ready'])
        self.assertEqual(set(result['checks']),{'provider_configured','docker_available'})

    def test_missing_provider_or_engine_is_not_ready(self):
        for failure in [FileNotFoundError(),subprocess.TimeoutExpired('docker',3)]:
            with patch('app.services.readiness.config.ACTIVE_LLM','unknown'),patch('app.services.readiness.subprocess.run',side_effect=failure):
                result=readiness()
            self.assertFalse(result['ready'])
            self.assertFalse(result['checks']['docker_available'])
            self.assertNotIn('api_key',str(result))

    def test_deployment_requires_token_and_built_ui(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':''}),patch('app.services.readiness.subprocess.run',return_value=subprocess.CompletedProcess([],0,'','')):
            result=readiness(require_token=True,frontend_dir=folder)
            self.assertFalse(result['checks']['access_token_configured'])
            self.assertFalse(result['checks']['frontend_built'])

    def test_preflight_reports_failure_without_provisioning(self):
        output=io.StringIO()
        with patch('app.tools.preflight.readiness',return_value={'ready':False,'checks':{}}) as check,redirect_stdout(output):
            self.assertEqual(preflight(['--deployment','--frontend-dir','/fixture']),1)
        self.assertEqual(check.call_args.kwargs,{'require_token':True,'frontend_dir':'/fixture'})
        self.assertIn('false',output.getvalue())


class DeploymentHttpTests(unittest.TestCase):
    def test_static_assets_and_fallback_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with TestClient(create_app(root)) as client:
                self.assertEqual(client.get('/').json()['message'],'Mini-Devin is running')
            (root/'index.html').write_text('<html><title>Fixture workspace</title></html>')
            (root/'assets').mkdir();(root/'assets/app.js').write_text('console.log("fixture")')
            with TestClient(create_app(root)) as client:
                self.assertIn('Fixture workspace',client.get('/').text)
                self.assertEqual(client.get('/assets/app.js').status_code,200)
                self.assertEqual(client.get('/assets/../.env').status_code,404)

    def test_health_status_codes_and_no_cache(self):
        with TestClient(create_app('/absent-frontend')) as client:
            self.assertEqual(client.get('/health/live').json(),{'status':'alive'})
            with patch('app.main.readiness',return_value={'ready':False,'checks':{'docker_available':False}}):
                response=client.get('/health/ready')
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.headers['cache-control'],'no-store')
            with patch('app.main.readiness',return_value={'ready':True,'checks':{}}):
                self.assertEqual(client.get('/health/ready').status_code,200)

    def test_all_original_and_prefixed_api_paths_require_access_token(self):
        with patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':'fixture-token'}),TestClient(create_app('/absent')) as client:
            for path in ['/chat','/chat/stream','/context/search','/api/chat','/api/chat/stream','/api/context/search']:
                with self.subTest(path=path):
                    response=client.post(path,json={'prompt':'hello','query':'hello'})
                    self.assertEqual(response.status_code,401)
                    self.assertEqual(response.headers['www-authenticate'],'Bearer')
            self.assertEqual(client.get('/health/live').status_code,200)

    def test_wrong_token_and_scheme_fail_cleanly(self):
        with patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':'fixture-token'}),TestClient(create_app('/absent')) as client:
            for token in ['Bearer wrong','Basic fixture-token']:
                self.assertEqual(client.post('/api/chat',headers={'Authorization':token},json={'prompt':'hi'}).status_code,401)

    def test_valid_token_reaches_request_validation(self):
        with patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':'fixture-token'}),TestClient(create_app('/absent')) as client:
            response=client.post('/api/chat',headers={'Authorization':'bearer fixture-token'},json={})
            self.assertEqual(response.status_code,422)


class AuthenticatedWorkflowTests(unittest.TestCase):
    setUp=test_orchestration.OrchestrationTests.setUp

    def test_protected_sync_and_stream_aliases_preserve_results(self):
        from tests.test_streaming import parse_events
        with patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':'fixture-token'}),TestClient(create_app('/absent')) as client:
            headers={'Authorization':'Bearer fixture-token'}
            response=client.post('/api/chat',headers=headers,json={'prompt':'hello'})
            streamed=client.post('/api/chat/stream',headers=headers,json={'prompt':'hello'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['attempts'][0]['success'])
        self.assertTrue(parse_events(streamed.text)[-1]['data']['success'])

    def test_unauthorized_request_never_calls_agent(self):
        with patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':'fixture-token'}),TestClient(create_app('/absent')) as client:
            client.post('/api/chat',json={'prompt':'hello'})
        self.mocks['plan_task'].assert_not_called()
