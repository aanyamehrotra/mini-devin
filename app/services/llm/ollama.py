"""Ollama adapter using the non-streaming local generation endpoint."""

import math
from urllib.parse import urlsplit

import requests

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from app.services.llm.base import BaseLLM


class OllamaLLM(BaseLLM):
    def __init__(self, base_url=None, model=None, timeout=None):
        self.base_url = (OLLAMA_BASE_URL if base_url is None else base_url).rstrip('/')
        self.model = (OLLAMA_MODEL if model is None else model).strip()
        url = urlsplit(self.base_url)
        if url.scheme not in ('http', 'https') or not url.netloc or url.query or url.fragment:
            raise ValueError('OLLAMA_BASE_URL must be an HTTP(S) URL without query or fragment')
        if not self.model:
            raise ValueError('OLLAMA_MODEL must name an installed model')
        try:
            self.timeout = float(OLLAMA_TIMEOUT if timeout is None else timeout)
        except (ValueError, TypeError):
            raise ValueError('OLLAMA_TIMEOUT must be a positive finite number') from None
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError('OLLAMA_TIMEOUT must be a positive finite number')

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                f'{self.base_url}/api/generate',
                json={'model': self.model, 'prompt': prompt, 'stream': False},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout:
            raise RuntimeError('Ollama generation timed out; check model capacity or OLLAMA_TIMEOUT') from None
        except requests.RequestException:
            raise RuntimeError('Ollama request failed; check the server, URL and installed model') from None
        try:
            data = response.json()
        except ValueError:
            raise RuntimeError('Ollama returned invalid JSON') from None
        if not isinstance(data, dict) or data.get('error'):
            raise RuntimeError('Ollama returned an invalid response or provider error')
        text = data.get('response')
        if data.get('done') is not True or not isinstance(text, str) or not text.strip():
            raise RuntimeError('Ollama returned incomplete or empty generated text')
        return text
