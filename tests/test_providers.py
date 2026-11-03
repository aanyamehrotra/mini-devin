import sys
import types
import unittest
from unittest.mock import Mock, patch

import requests

from app.services.llm import factory
from app.services.llm.ollama import OllamaLLM


class OllamaTests(unittest.TestCase):
    def setUp(self):
        self.llm = OllamaLLM(base_url='http://localhost:11434/', model='test-model', timeout=3)

    @patch('app.services.llm.ollama.requests.post')
    def test_generation_contract(self, post):
        post.return_value.json.return_value = {'response': 'print("hello")', 'done': True}
        self.assertEqual(self.llm.generate('write hello'), 'print("hello")')
        post.assert_called_once_with('http://localhost:11434/api/generate',
                                     json={'model': 'test-model', 'prompt': 'write hello', 'stream': False},
                                     timeout=3.0)
        post.return_value.raise_for_status.assert_called_once()

    @patch('app.services.llm.ollama.requests.post')
    def test_transport_failures(self, post):
        for error, message in [(requests.Timeout(), 'timed out'),
                               (requests.ConnectionError(), 'request failed'),
                               (requests.HTTPError(), 'request failed')]:
            with self.subTest(error=type(error).__name__):
                post.side_effect = error
                with self.assertRaisesRegex(RuntimeError, message):
                    self.llm.generate('task')

    @patch('app.services.llm.ollama.requests.post')
    def test_http_failure_checked_before_json(self, post):
        post.return_value.raise_for_status.side_effect = requests.HTTPError()
        with self.assertRaisesRegex(RuntimeError, 'request failed'):
            self.llm.generate('task')
        post.return_value.json.assert_not_called()

    @patch('app.services.llm.ollama.requests.post')
    def test_bad_responses(self, post):
        for data in [[], None, {'error': 'missing model'}, {'response': 42, 'done': True},
                     {'response': '', 'done': True}, {'response': '  ', 'done': True},
                     {'response': 'partial', 'done': False}, {'response': 'missing done'}]:
            with self.subTest(data=data):
                post.return_value.json.return_value = data
                with self.assertRaises(RuntimeError):
                    self.llm.generate('task')

    @patch('app.services.llm.ollama.requests.post')
    def test_invalid_json(self, post):
        post.return_value.json.side_effect = ValueError('bad json')
        with self.assertRaisesRegex(RuntimeError, 'invalid JSON'):
            self.llm.generate('task')

    def test_invalid_configuration(self):
        for kwargs in [{'model': ' '}, {'base_url': 'file:///tmp'},
                       {'base_url': 'http://localhost?secret=x'},
                       *({'timeout': value} for value in [0, -1, 'bad', 'nan', 'inf'])]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                OllamaLLM(**kwargs)


class FactoryTests(unittest.TestCase):
    def test_provider_dispatch_is_lazy(self):
        for name, class_name in [('gemini', 'GeminiLLM'), ('groq', 'GroqLLM'), ('ollama', 'OllamaLLM')]:
            constructor = Mock()
            module = types.ModuleType('provider_stub')
            setattr(module, class_name, constructor)
            with self.subTest(name=name), patch.object(factory, 'ACTIVE_LLM', f' {name.upper()} '), patch.dict(
                sys.modules, {f'app.services.llm.{name}': module}
            ):
                self.assertIs(factory.get_llm(), constructor.return_value)
                constructor.assert_called_once_with()

    def test_unknown_provider(self):
        with patch.object(factory, 'ACTIVE_LLM', 'unknown'), self.assertRaisesRegex(ValueError, 'Unsupported provider'):
            factory.get_llm()
