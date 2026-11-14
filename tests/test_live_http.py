"""Explicit real-model + Docker + production-asset HTTP checks; opt-in only."""
import json
import os
import re
import secrets
import socket
import threading
import time
import unittest
from unittest.mock import patch
import requests


@unittest.skipUnless(os.getenv('MINI_DEVIN_LIVE_HTTP')=='1','Live model HTTP checks are opt-in')
class LiveHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import uvicorn
        from app.main import create_app
        cls.token=secrets.token_urlsafe(32)
        cls.env=patch.dict(os.environ,{'MINI_DEVIN_API_TOKEN':cls.token})
        cls.env.start()
        cls.sock=socket.socket()
        cls.sock.bind(('127.0.0.1',0))
        cls.url=f'http://127.0.0.1:{cls.sock.getsockname()[1]}'
        cls.server=uvicorn.Server(uvicorn.Config(create_app(),log_level='error',access_log=False))
        cls.thread=threading.Thread(target=lambda:cls.server.run(sockets=[cls.sock]),daemon=True)
        cls.thread.start()
        for _ in range(100):
            if cls.server.started:break
            time.sleep(.05)
        if not cls.server.started:
            cls.env.stop()
            raise RuntimeError('Local HTTP server did not start')

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit=True
        cls.thread.join(timeout=10)
        cls.sock.close()
        cls.env.stop()

    def test_production_assets_health_and_unauthorized_request(self):
        home=requests.get(self.url+'/',timeout=5)
        self.assertEqual(home.status_code,200)
        self.assertIn('text/html',home.headers['content-type'])
        script=re.search(r'src="([^"]+\.js)"',home.text)
        self.assertIsNotNone(script)
        self.assertEqual(requests.get(self.url+script.group(1),timeout=5).status_code,200)
        self.assertEqual(requests.get(self.url+'/health/live',timeout=5).status_code,200)
        ready=requests.get(self.url+'/health/ready',timeout=10)
        self.assertEqual(ready.status_code,200)
        self.assertTrue(ready.json()['ready'])
        denied=requests.post(self.url+'/api/chat',json={'prompt':'Do not run'},timeout=5)
        self.assertEqual(denied.status_code,401)

    def test_authenticated_real_provider_and_docker_stream(self):
        prompt='Create a Python program that prints exactly MINI_DEVIN_DEPLOY_OK on one line. Use the standard library only, no user input or external dependencies.'
        with requests.post(self.url+'/api/chat/stream',headers={'Authorization':'Bearer '+self.token},
                           json={'prompt':prompt},stream=True,timeout=(5,120)) as response:
            self.assertEqual(response.status_code,200)
            events=[]; event_type=None
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('event: '):event_type=line[7:]
                if line.startswith('data: '):events.append((event_type,json.loads(line[6:])))
                if events and events[-1][0] in {'complete','error','cancelled'}:break
        self.assertEqual(events[0][0],'started')
        self.assertEqual(events[-1][0],'complete')
        self.assertTrue(events[-1][1]['success'])
        result=events[-1][1]['result']
        self.assertEqual(result['execution']['stdout'].strip(),'MINI_DEVIN_DEPLOY_OK')
        self.assertTrue(result['review']['success'])
        self.assertEqual([data['stage'] for kind,data in events if kind=='stage'][:4],['plan','generate','execute','review'])
