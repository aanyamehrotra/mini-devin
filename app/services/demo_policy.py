"""Per-request limits propagated through the demo's agent worker."""
from contextvars import ContextVar

public_demo = ContextVar('public_demo', default=False)
