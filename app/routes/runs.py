import re
import sqlite3
from fastapi import APIRouter, HTTPException, Response
from app.storage.runs import list_runs, get_run

router=APIRouter()


@router.get('/runs')
def runs(response:Response):
    response.headers["Cache-Control"]="no-store"
    try:
        return {'runs':list_runs()}
    except (OSError,sqlite3.Error):
        raise HTTPException(status_code=503,detail='Saved runs are unavailable') from None


@router.get('/runs/{identifier}')
def run(identifier:str,response:Response):
    response.headers["Cache-Control"]="no-store"
    if not re.fullmatch(r'[0-9a-f]{32}',identifier):
        raise HTTPException(status_code=404,detail='Run not found')
    try:
        saved=get_run(identifier)
    except (OSError,sqlite3.Error):
        raise HTTPException(status_code=503,detail='Saved runs are unavailable') from None
    if saved is None:
        raise HTTPException(status_code=404,detail='Run not found')
    return saved
