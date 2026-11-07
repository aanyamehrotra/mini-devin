import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from app.executor.runner import execute_code
from app.models.schemas import CodeResponse, GeneratedFile


class MultiFileTests(unittest.TestCase):
    def setUp(self):
        self.previous = Path.cwd()
        self.temp = tempfile.TemporaryDirectory()
        os.chdir(self.temp.name)
        self.addCleanup(self.restore)

    def restore(self):
        os.chdir(self.previous)
        self.temp.cleanup()

    def project(self, entries):
        return CodeResponse(files=[GeneratedFile(path=p, content=c) for p, c in entries])

    @patch('app.executor.runner.run_in_docker')
    @patch('app.executor.runner.validate_in_docker')
    def test_nested_project_writes_all_files_and_uses_nested_entry(self, validate, run):
        validate.return_value = subprocess.CompletedProcess([], 0, '', '')
        run.return_value = subprocess.CompletedProcess([], 0, '42\n', '')
        result = execute_code(self.project([('src/main.py', 'from helpers import answer\nprint(answer)'),
                                            ('src/helpers.py', 'answer = 42')]))
        self.assertTrue(result.success)
        self.assertEqual(result.stdout, '42\n')
        root, entry = run.call_args.args
        self.assertEqual(entry, Path('src/main.py'))
        self.assertEqual((root / 'src/helpers.py').read_text(), 'answer = 42')
        self.assertEqual(len(validate.call_args.args[1]), 2)

    @patch('app.executor.runner.run_in_docker')
    @patch('app.executor.runner.validate_in_docker')
    def test_library_is_compiled_without_execution(self, validate, run):
        validate.return_value = subprocess.CompletedProcess([], 0, '', '')
        result = execute_code(self.project([('lib/helper.py', 'answer = 42')]))
        self.assertTrue(result.success)
        validate.assert_called_once()
        run.assert_not_called()

    @patch('app.executor.runner.run_in_docker')
    @patch('app.executor.runner.validate_in_docker')
    def test_empty_or_non_python_project_is_not_success(self, validate, run):
        for entries in [[], [('README.md', 'no code')]]:
            with self.subTest(entries=entries):
                result = execute_code(self.project(entries))
                self.assertFalse(result.success)
                self.assertEqual(result.error_type, 'UnsupportedProject')
        validate.assert_not_called()
        run.assert_not_called()

    @patch('app.executor.runner.run_in_docker')
    @patch('app.executor.runner.validate_in_docker')
    def test_syntax_failure_stops_runtime(self, validate, run):
        validate.return_value = subprocess.CompletedProcess([], 1, '', 'SyntaxError: invalid')
        result = execute_code(self.project([('main.py', 'bad syntax')]))
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, 'SyntaxError')
        run.assert_not_called()

    @patch('app.executor.runner.run_in_docker')
    @patch('app.executor.runner.validate_in_docker')
    def test_repeated_execution_uses_distinct_workspaces(self, validate, run):
        validate.return_value = subprocess.CompletedProcess([], 0, '', '')
        run.return_value = subprocess.CompletedProcess([], 0, '', '')
        project = self.project([('main.py', 'pass')])
        execute_code(project)
        execute_code(project)
        self.assertNotEqual(run.call_args_list[0].args[0], run.call_args_list[1].args[0])
