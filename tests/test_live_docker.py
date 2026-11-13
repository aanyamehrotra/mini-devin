"""Opt-in real engine checks: MINI_DEVIN_LIVE_DOCKER=1 python -m unittest tests.test_live_docker -v."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from app.executor.runner import execute_code
from app.models.schemas import CodeResponse, GeneratedFile


@unittest.skipUnless(os.getenv('MINI_DEVIN_LIVE_DOCKER') == '1', 'Live Docker checks are opt-in')
class LiveDockerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        check = subprocess.run(['docker','info'],capture_output=True,timeout=20)
        if check.returncode:
            raise RuntimeError('Docker service must be running for requested live checks')

    def setUp(self):
        self.previous = Path.cwd()
        self.temp = tempfile.TemporaryDirectory()
        os.chdir(self.temp.name)
        self.addCleanup(self.restore)

    def restore(self):
        os.chdir(self.previous)
        self.temp.cleanup()

    def execute(self, files):
        return execute_code(CodeResponse(files=[GeneratedFile(path=p,content=c) for p,c in files]))

    def test_multifile_nested_import(self):
        result=self.execute([('src/main.py','from helpers import answer\nprint(answer)'),('src/helpers.py','answer = 42')])
        self.assertTrue(result.success,result.stderr)
        self.assertEqual(result.stdout.strip(),'42')

    def test_library_compiles(self):
        result=self.execute([('lib/helpers.py','def answer():\n    return 42')])
        self.assertTrue(result.success,result.stderr)
        self.assertIn('module/library',result.stdout)

    def test_syntax_error_is_classified(self):
        result=self.execute([('main.py','def broken(:')])
        self.assertFalse(result.success)
        self.assertEqual(result.error_type,'SyntaxError')

    def test_runtime_error_is_classified(self):
        result=self.execute([('main.py','raise ValueError("fixture error")')])
        self.assertFalse(result.success)
        self.assertEqual(result.error_type,'ValueError')

    def test_runtime_network_is_unavailable(self):
        result=self.execute([('main.py','''import socket
try:
    socket.create_connection(('1.1.1.1', 53), timeout=1)
except OSError:
    print('NETWORK_DENIED')
else:
    raise RuntimeError('Unexpected network access')
''')])
        self.assertTrue(result.success,result.stderr)
        self.assertEqual(result.stdout.strip(),'NETWORK_DENIED')

    def test_installed_dependency_imports(self):
        result=self.execute([('main.py','import requests\nprint(requests.__version__)'),('requirements.txt','requests==2.31.0')])
        self.assertTrue(result.success,result.stderr)
        self.assertEqual(result.stdout.strip(),'2.31.0')

    def test_timeout_removes_new_containers(self):
        def containers():
            result=subprocess.run(['docker','ps','--filter','name=mini-devin-','--format','{{.Names}}'],
                                  capture_output=True,text=True,timeout=10,check=True)
            return set(result.stdout.splitlines())
        before=containers()
        result=self.execute([('main.py','while True:\n    pass')])
        self.assertFalse(result.success)
        self.assertEqual(result.error_type,'Timeout')
        self.assertFalse(containers()-before,'A timed-out container survived cleanup')
