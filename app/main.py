import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.routes.chat import router as chat_router
from app.routes.context import router as context_router
from app.services.access import BearerGuard
from app.services.readiness import readiness


def create_app(frontend_dir=None):
    application = FastAPI()
    root = Path(frontend_dir or os.getenv('FRONTEND_DIST', Path(__file__).resolve().parents[1] / 'frontend/dist'))
    application.add_middleware(BearerGuard)

    @application.get('/')
    def home():
        if (root / 'index.html').is_file():
            return FileResponse(root / 'index.html', headers={'Cache-Control':'no-cache'})
        return {'message':'Mini-Devin is running'}

    @application.get('/health/live')
    def live():
        return {'status':'alive'}

    @application.get('/health/ready')
    def ready():
        result = readiness()
        return JSONResponse(result, status_code=200 if result['ready'] else 503,
                            headers={'Cache-Control':'no-store'})

    application.include_router(chat_router)
    application.include_router(context_router)
    application.include_router(chat_router, prefix='/api')
    application.include_router(context_router, prefix='/api')
    if (root / 'assets').is_dir():
        application.mount('/assets', StaticFiles(directory=root / 'assets'), name='frontend-assets')
    return application


app = create_app()
