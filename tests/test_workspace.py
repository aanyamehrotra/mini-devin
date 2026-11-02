import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.executor.workspace import resolve_project_files


def files(*paths):
    return [SimpleNamespace(path=path, content='print("hello")') for path in paths]


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_nested_files(self):
        result = resolve_project_files(self.root, files('main.py', 'src/helpers.py'))
        self.assertEqual(result[1][0], self.root.resolve() / 'src/helpers.py')

    def test_unsafe_paths(self):
        for path in ('../escape.py', 'src/../../escape.py', '/tmp/escape.py',
                     'C:/escape.py', 'C:escape.py', r'..\escape.py', '', '.', ' ', 'bad\x00.py'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                resolve_project_files(self.root, files(path))

    def test_duplicates(self):
        with self.assertRaises(ValueError):
            resolve_project_files(self.root, files('src/main.py', 'src/./main.py'))

    def test_file_directory_conflict(self):
        for paths in [('src', 'src/main.py'), ('src/main.py', 'src')]:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                resolve_project_files(self.root, files(*paths))

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.root / 'link').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                resolve_project_files(self.root, files('link/escape.py'))

    def test_validation_does_not_write_partial_batch(self):
        with self.assertRaises(ValueError):
            resolve_project_files(self.root, files('valid.py', '../escape.py'))
        self.assertFalse((self.root / 'valid.py').exists())


class ExecutorPathTests(unittest.TestCase):
    def test_invalid_project_never_reaches_docker(self):
        import os
        from unittest.mock import patch
        from app.executor.runner import execute_code
        from app.models.schemas import CodeResponse, GeneratedFile
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                project = CodeResponse(files=[
                    GeneratedFile(path="valid.py", content="pass"),
                    GeneratedFile(path="../escape.py", content="pass"),
                ])
                with patch("app.executor.runner.validate_in_docker") as validate:
                    result = execute_code(project)
                self.assertFalse(result.success)
                self.assertEqual(result.error_type, "InvalidProjectPath")
                validate.assert_not_called()
                self.assertEqual(list(Path(directory).rglob("*.py")), [])
            finally:
                os.chdir(previous)
