"""Owner-only execution of edited projects; never exposes host filesystem paths."""
import time
from fastapi import APIRouter, Response
from app.models.schemas import CodeResponse
from app.executor.runner import execute_code

router = APIRouter(prefix='/api/projects')


@router.post('/execute')
def execute_project(project: CodeResponse, response: Response):
    response.headers["Cache-Control"]="no-store"
    started = time.perf_counter()
    execution = execute_code(project)
    return {'code': project.model_dump(), 'execution': execution.model_dump(),
            'review': {'success': execution.success, 'feedback': 'Manual execution only. No AI review was requested.', 'mode': 'not_requested'},
            'success': execution.success,
            'duration_ms': round((time.perf_counter()-started)*1000)}
