import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.executor.requirements import validate_requirements, InvalidRequirementsError
from app.executor.docker_runner import run_in_docker


class RequirementsTests(unittest.TestCase):
    def test_package_names_extras_and_versions(self):
        self.assertTrue(validate_requirements('requests>=2.31,<3\nuvicorn[standard]==0.24.0 # example\nnumpy'))

    def test_empty_and_comment_only_files_need_no_install(self):
        self.assertFalse(validate_requirements('  \n# no dependencies\n'))

    def test_sources_and_options_are_rejected(self):
        for value in ['-r other.txt', '--index-url https://evil.test', '-e .', '.',
                      './project', '/tmp/project', 'pkg @ https://example.test/pkg.whl',
                      'https://example.test/pkg.whl', 'git+https://example.test/pkg',
                      'pkg; python_version > "3"', 'pkg \\','pkg --config-settings=x']:
            with self.subTest(value=value), self.assertRaises(InvalidRequirementsError):
                validate_requirements(value)

    @patch('app.executor.docker_runner._run')
    def test_invalid_requirement_prevents_container_launch(self, run):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'requirements.txt').write_text('-e .')
            with self.assertRaises(InvalidRequirementsError):
                run_in_docker(folder, 'main.py')
        run.assert_not_called()
