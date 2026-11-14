"""Optional shared-token guard that preserves the ASGI streaming lifecycle."""
import hmac
import os
from starlette.responses import JSONResponse


class BearerGuard:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get('path','')
        protected = path.startswith('/api/') or path in {'/chat','/chat/stream','/context/search'}
        token = os.getenv('MINI_DEVIN_API_TOKEN','')
        if scope['type'] == 'http' and protected and token:
            header = dict(scope.get('headers',[])).get(b'authorization',b'')
            scheme, _, supplied = header.partition(b' ')
            allowed = scheme.lower() == b'bearer' and hmac.compare_digest(supplied,token.encode())
            if not allowed:
                response = JSONResponse({'detail':'Workspace access token required'},status_code=401,
                                        headers={'WWW-Authenticate':'Bearer','Cache-Control':'no-store'})
                await response(scope,receive,send)
                return
        await self.app(scope,receive,send)
