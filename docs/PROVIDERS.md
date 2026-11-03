# LLM providers

Select `groq`, `gemini` or `ollama` using `ACTIVE_LLM` in your environment or
local `.env`. Provider names ignore case and surrounding whitespace. Gemini and
Groq use `GEMINI_API_KEY` and `GROQ_API_KEY` respectively. Do not commit secrets.

## Ollama

1. Install and start Ollama on your machine.
2. Pull the model you intend to use, for example `ollama pull qwen2.5-coder:7b`.
   Choose a model that fits your hardware; the example is configurable and is not
   downloaded automatically by Mini-Devin.
3. Copy `.env.example` to `.env`, or set these variables in the environment:

```dotenv
ACTIVE_LLM=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_TIMEOUT=120
```

`OLLAMA_TIMEOUT` is a positive, finite number of seconds. The URL must use HTTP
or HTTPS and have no query or fragment. Use a trusted Ollama server: generated
prompts are sent to that configured server. If Mini-Devin runs inside a container,
localhost refers to that container; configure a reachable Ollama server URL.

The adapter uses Ollama's [generate API](https://docs.ollama.com/api/generate)
with `stream=false` to implement the existing synchronous `generate(prompt) -> str`
interface. Incomplete or empty responses, invalid JSON, connection errors, HTTP
failures and timeouts produce explicit errors. This adapter does not implement
frontend streaming, automatic downloads, or retries.

## Validation

Run the offline suite without API keys or a running model server:

```sh
python3 -m unittest discover -s tests -v
```

The provider dispatch checks use constructor stubs for all three providers;
Ollama transport checks mock HTTP responses. These do not prove Gemini/Groq SDK
compatibility or live model quality. For an explicitly requested live check,
after installing requirements and configuring your selected provider, run:

```sh
python3 -m tests.test_llm
```

That manual check invokes the selected real provider and may incur provider costs.
