import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.executor.docker_runner import run_in_docker, validate_in_docker


class DockerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.main = self.root / 'main.py'
        self.main.write_text('print("hello")')

    @patch('app.executor.docker_runner.subprocess.run')
    def test_runtime_is_bounded_and_network_disabled(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, 'hello', '')
        run_in_docker(self.root, 'main.py')
        command = run.call_args_list[0].args[0]
        for flag in ['--read-only', '--init', '--cap-drop', '--user', '--memory-swap']:
            self.assertIn(flag, command)
        self.assertEqual(command[command.index('--network')+1], 'none')
        self.assertEqual(command[-2:], ['python', './main.py'])
        self.assertEqual(run.call_args_list[0].kwargs['stdin'], subprocess.DEVNULL)
        self.assertEqual(run.call_args_list[1].args[0], ['docker', 'rm', '-f', command[command.index('--name')+1]])

    @patch('app.executor.docker_runner.subprocess.run')
    def test_timeout_cleans_container_and_preserves_error(self, run):
        run.side_effect = [subprocess.TimeoutExpired('docker', 30), subprocess.CompletedProcess([], 0, '', '')]
        with self.assertRaises(subprocess.TimeoutExpired):
            run_in_docker(self.root, 'main.py')
        self.assertEqual(run.call_args_list[1].args[0][:3], ['docker', 'rm', '-f'])

    @patch('app.executor.docker_runner.subprocess.run')
    def test_cleanup_failure_does_not_hide_result(self, run):
        result = subprocess.CompletedProcess([], 1, '', 'program error')
        run.side_effect = [result, subprocess.TimeoutExpired('docker', 5)]
        with self.assertLogs('app.executor.docker_runner', level='WARNING'):
            self.assertIs(run_in_docker(self.root, 'main.py'), result)

    @patch('app.executor.docker_runner._run')
    def test_dependency_runtime_is_separate_and_network_disabled(self, run):
        (self.root / 'requirements.txt').write_text('requests')
        entry = 'nested; touch BAD/main.py'
        run.return_value = subprocess.CompletedProcess([], 0, '', '')
        run_in_docker(self.root, entry)
        installer, runtime = run.call_args_list
        self.assertEqual(installer.kwargs['network'], 'bridge')
        self.assertTrue(installer.kwargs['install'])
        self.assertIn('--only-binary=:all:', installer.args[1])
        self.assertNotIn(entry, installer.args[1])
        self.assertEqual(runtime.args[1], ['python', './'+entry])
        self.assertNotIn('network', runtime.kwargs)  # _run defaults to none
        self.assertNotIn('install', runtime.kwargs)
        self.assertEqual(installer.kwargs['dependencies'], runtime.kwargs['dependencies'])
        self.assertFalse(Path(runtime.kwargs['dependencies']).exists())

    @patch('app.executor.docker_runner._run')
    def test_dependency_install_failure_stops_execution(self, run):
        (self.root / 'requirements.txt').write_text('missing-package')
        failed = subprocess.CompletedProcess([], 1, '', 'install failed')
        run.return_value = failed
        self.assertIs(run_in_docker(self.root, 'main.py'), failed)
        run.assert_called_once()

    @patch('app.executor.docker_runner.subprocess.run')
    def test_dependency_mount_read_only_at_runtime(self, run):
        from app.executor.docker_runner import _run
        run.return_value = subprocess.CompletedProcess([], 0, '', '')
        _run(self.root, ['python', './main.py'], dependencies=self.root)
        command = run.call_args_list[0].args[0]
        self.assertIn(f'{self.root.resolve()}:/deps:ro', command)

    @patch('app.executor.docker_runner.subprocess.run')
    def test_validation_uses_network_none(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, '', '')
        validate_in_docker(self.root, [self.main])
        command = run.call_args_list[0].args[0]
        self.assertEqual(command[-4:], ['python', '-m', 'py_compile', 'main.py'])
        self.assertEqual(command[command.index('--network')+1], 'none')

    @patch('app.executor.docker_runner.subprocess.run')
    def test_entry_escape_rejected_before_launch(self, run):
        with self.assertRaises(ValueError):
            run_in_docker(self.root, '../outside.py')
        run.assert_not_called()


class ExecutorEnvironmentTests(unittest.TestCase):
    def execute(self, result=None, error=None):
        import os
        from app.executor.runner import execute_code
        from app.models.schemas import CodeResponse, GeneratedFile
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                with patch('app.executor.runner.validate_in_docker', return_value=result, side_effect=error):
                    return execute_code(CodeResponse(files=[GeneratedFile(path='main.py', content='pass')]))
            finally:
                os.chdir(previous)

    def test_missing_docker_returns_environment_failure(self):
        result = self.execute(error=FileNotFoundError('docker'))
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'ExecutionEnvironment')

    def test_docker_start_failure_is_not_syntax_error(self):
        result = self.execute(result=subprocess.CompletedProcess([], 125, '', 'daemon unavailable'))
        self.assertEqual(result.error_type, 'ExecutionEnvironment')

    def test_python_validation_error_preserved(self):
        result = self.execute(result=subprocess.CompletedProcess([], 1, '', 'SyntaxError: invalid'))
        self.assertEqual(result.error_type, 'SyntaxError')
