"""Private single-workspace SQLite archive with bounded retention."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone
import uuid

MAX_RUNS=100
MAX_RESULT_BYTES=5*1024*1024


@contextmanager
def _connect():
    path=Path(os.getenv('MINI_DEVIN_HISTORY_DB',Path(__file__).resolve().parents[2]/'data/runs.sqlite3'))
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    connection=sqlite3.connect(path,timeout=5)
    os.chmod(path,0o600)
    connection.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, prompt TEXT NOT NULL, success INTEGER NOT NULL, goal TEXT NOT NULL, result TEXT NOT NULL)')
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def save_run(prompt,result):
    payload=json.dumps(result,ensure_ascii=False)
    if len(payload.encode())>MAX_RESULT_BYTES:
        raise ValueError('Run exceeds archive size limit')
    identifier=uuid.uuid4().hex
    created=datetime.now(timezone.utc).isoformat()
    success=bool(result.get('attempts') and result['attempts'][-1]['success'])
    goal=result.get('plan',{}).get('goal','Generated project')
    with _connect() as connection:
        connection.execute('INSERT INTO runs VALUES (?,?,?,?,?,?)',(identifier,created,prompt,int(success),goal,payload))
        connection.execute('DELETE FROM runs WHERE id NOT IN (SELECT id FROM runs ORDER BY created_at DESC,id DESC LIMIT ?)',(MAX_RUNS,))
    return identifier


def list_runs():
    with _connect() as connection:
        rows=connection.execute('SELECT id,created_at,success,goal FROM runs ORDER BY created_at DESC,id DESC LIMIT 50').fetchall()
    return [{'id':r[0],'created_at':r[1],'success':bool(r[2]),'goal':r[3]} for r in rows]


def get_run(identifier):
    with _connect() as connection:
        row=connection.execute('SELECT id,created_at,prompt,result FROM runs WHERE id=?',(identifier,)).fetchone()
    if not row:
        return None
    result=json.loads(row[3]);result['run_id']=row[0]
    return {'id':row[0],'created_at':row[1],'prompt':row[2],'result':result}
