"""No-charge configuration/engine checks; never call a billable model endpoint."""
import os
from pathlib import Path
import subprocess
from app import config


def readiness(*, require_token=False, frontend_dir=None):
    provider = config.ACTIVE_LLM.strip().lower()
    configured = {
        'groq': bool(config.GROQ_API_KEY and config.GROQ_MODEL),
        'gemini': bool(config.GEMINI_API_KEY),
        'ollama': bool(config.OLLAMA_BASE_URL and config.OLLAMA_MODEL),
    }.get(provider, False)
    try:
        engine = subprocess.run(['docker','info','--format','{{.ServerVersion}}'],
                                capture_output=True, text=True, timeout=3)
        docker_ready = engine.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        docker_ready = False
    checks = {'provider_configured': configured, 'docker_available': docker_ready}
    if require_token:
        checks['access_token_configured'] = len(os.getenv('MINI_DEVIN_API_TOKEN','')) >= 32
    if frontend_dir is not None:
        root = Path(frontend_dir)
        checks['frontend_built'] = (root / 'index.html').is_file() and (root / 'assets').is_dir()
    return {'ready': all(checks.values()), 'checks': checks}
