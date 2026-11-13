import unittest
from unittest.mock import Mock, patch
from app.services.llm.groq import GroqLLM


class GroqConfigurationTests(unittest.TestCase):
    def test_configured_model_and_bounded_client_settings(self):
        response=Mock()
        response.choices=[Mock(message=Mock(content='hello'))]
        with patch('app.services.llm.groq.Groq') as constructor, patch('app.services.llm.groq.GROQ_MODEL','configured-model'):
            constructor.return_value.chat.completions.create.return_value=response
            self.assertEqual(GroqLLM().generate('hello'),'hello')
            self.assertEqual(constructor.call_args.kwargs['timeout'],30)
            self.assertEqual(constructor.call_args.kwargs['max_retries'],0)
            self.assertEqual(constructor.return_value.chat.completions.create.call_args.kwargs['model'],'configured-model')
