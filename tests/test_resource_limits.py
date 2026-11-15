import unittest
from pydantic import ValidationError
from app.models.schemas import ChatRequest,CodeResponse,GeneratedFile
from app.executor.runner import _execution_slot,execute_code


class ResourceLimitTests(unittest.TestCase):
    def test_prompt_and_file_limits(self):
        with self.assertRaises(ValidationError):ChatRequest(prompt='x'*20001)
        with self.assertRaises(ValidationError):GeneratedFile(path='a.py',content='x'*262145)
        with self.assertRaises(ValidationError):CodeResponse(files=[GeneratedFile(path='a.py',content='')]*101)

    def test_total_utf8_content_limit(self):
        with self.assertRaises(ValidationError):
            CodeResponse(files=[GeneratedFile(path=f'{i}.py',content='🐍'*100000) for i in range(3)])

    def test_busy_execution_slot_returns_environment_failure(self):
        _execution_slot.acquire()
        try:
            result=execute_code(CodeResponse(files=[]))
            self.assertEqual(result.error_type,'ExecutionEnvironment')
        finally:_execution_slot.release()

    def test_dependency_volume_quota_and_cleanup(self):
        from unittest.mock import patch
        from subprocess import CompletedProcess
        from app.executor.docker_runner import dependency_volume
        with patch('app.executor.docker_runner.capture_output',return_value=CompletedProcess([],0,'','')) as run:
            with dependency_volume() as name:
                self.assertTrue(name.startswith('mini-devin-deps-'))
            self.assertIn('type=tmpfs',run.call_args_list[0].args[0])
            self.assertTrue(any('size=128m' in p for p in run.call_args_list[0].args[0]))
            self.assertEqual(run.call_args_list[-1].args[0],['docker','volume','rm','-f',name])

    def test_failed_volume_setup_never_yields(self):
        from unittest.mock import patch
        from subprocess import CompletedProcess
        from app.executor.docker_runner import dependency_volume
        with patch('app.executor.docker_runner.capture_output',return_value=CompletedProcess([],1,'','no such volume')):
            with self.assertRaises(OSError):
                with dependency_volume():self.fail('Failed setup yielded')

    def test_source_workspace_retention_preserves_unrelated_directories(self):
        import os,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from subprocess import CompletedProcess
        previous=Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                Path('workspace/user-files').mkdir(parents=True)
                with patch('app.executor.runner.validate_in_docker',return_value=CompletedProcess([],0,'','')):
                    for _ in range(22):
                        execute_code(CodeResponse(files=[GeneratedFile(path='library.py',content='pass')]))
                self.assertTrue(Path('workspace/user-files').is_dir())
                self.assertLessEqual(len([p for p in Path('workspace').iterdir() if p.name!='user-files']),20)
            finally:os.chdir(previous)
