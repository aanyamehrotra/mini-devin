"""Opt-in public examples, separate from the private workspace and archive."""
import asyncio
from datetime import datetime, timezone
import hashlib
import hmac
import ipaddress
import json
import os
from pathlib import Path
import queue
import sqlite3
import threading
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from app.agents.manager import stream_agent
from app.services.demo_policy import public_demo
from app.services.llm.structured import AgentResponseError
from app.evaluation.runner import tasks

router = APIRouter(prefix='/demo')
TASKS = {
    'fibonacci': 'Create main.py that prints exactly the first 10 Fibonacci numbers starting with 0 and 1, separated by spaces, on one line. Standard library only, no dependencies, no input or networking.',
    'csv': 'Create main.py using only the Python standard library. Parse the inline CSV string "name,score\\nAanya,80\\nSam,90\\nLee,100\\n" with csv.DictReader and print exactly "Average score: 90.0". No input, external files, networking or dependencies.',
}
TASKS.update({task['id']: task['prompt'] for task in tasks() if task['id'] in {'csv-quality', 'log-analyzer', 'average-fix'}})
DAILY_TOTAL = 20
DAILY_VISITOR = 3
COOLDOWN = 60
GLOBAL_COOLDOWN = 60
LEASE_SECONDS = 600


class DemoRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    task: str


def _enabled():
    # Never open the private APIs as a side effect of enabling the demo.
    if os.getenv('MINI_DEVIN_PUBLIC_DEMO') != '1' or len(os.getenv('MINI_DEVIN_API_TOKEN', '')) < 32:
        raise HTTPException(404, 'Public demo is unavailable')


def _visitor(request):
    address = request.client.host if request.client else 'unknown'
    try:
        ip = ipaddress.ip_address(address)
        address = str(ipaddress.ip_network(f'{ip}/64', strict=False)) if ip.version == 6 else str(ip)
    except ValueError:
        pass
    return hmac.new(os.environ['MINI_DEVIN_API_TOKEN'].encode(), address.encode(), hashlib.sha256).hexdigest()


def _connect():
    path = Path(os.getenv('MINI_DEVIN_DEMO_DB', Path(__file__).resolve().parents[2] / 'data/demo-quota.sqlite3'))
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=5)
    os.chmod(path, 0o600)
    db.execute('CREATE TABLE IF NOT EXISTS quota (day TEXT, visitor TEXT, count INTEGER, last REAL, PRIMARY KEY(day,visitor))')
    db.execute('CREATE TABLE IF NOT EXISTS active (slot INTEGER PRIMARY KEY, ticket TEXT, started REAL)')
    return db


def _reserve(visitor):
    now = time.time()
    day = datetime.fromtimestamp(now, timezone.utc).date().isoformat()
    db = _connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM quota WHERE day < ?', (day,))
        active = db.execute('SELECT started FROM active WHERE slot=1').fetchone()
        if active and now - active[0] < LEASE_SECONDS:
            raise HTTPException(429, 'The demo is helping another visitor. Try again shortly.', headers={'Retry-After': '30'})
        total, last_global = db.execute('SELECT COALESCE(SUM(count),0),MAX(last) FROM quota WHERE day=?', (day,)).fetchone()
        row = db.execute('SELECT count,last FROM quota WHERE day=? AND visitor=?', (day, visitor)).fetchone()
        if total >= DAILY_TOTAL:
            raise HTTPException(429, 'Today’s demo limit has been reached. Please try tomorrow.', headers={'Retry-After': '3600'})
        if row and row[0] >= DAILY_VISITOR:
            raise HTTPException(429, 'You’ve used today’s three demo runs. Please try tomorrow.', headers={'Retry-After': '3600'})
        if row and now - row[1] < COOLDOWN:
            raise HTTPException(429, 'Please wait a minute between demo runs.', headers={'Retry-After': str(max(1, int(COOLDOWN - (now - row[1]))))})
        if last_global and now - last_global < GLOBAL_COOLDOWN:
            raise HTTPException(429, 'The live demo is cooling down to respect free model limits. Explore a completed project while you wait.', headers={'Retry-After': str(max(1, int(GLOBAL_COOLDOWN - (now-last_global))))})
        ticket = uuid.uuid4().hex
        db.execute('INSERT OR REPLACE INTO active VALUES (1,?,?)', (ticket, now))
        db.execute('INSERT INTO quota VALUES (?,?,1,?) ON CONFLICT(day,visitor) DO UPDATE SET count=count+1,last=excluded.last', (day, visitor, now))
        db.commit()
        return ticket
    finally:
        db.close()


def _release(ticket):
    db = _connect()
    try:
        with db:
            db.execute('DELETE FROM active WHERE slot=1 AND ticket=?', (ticket,))
    finally:
        db.close()


def _work(task, ticket, messages):
    async def run():
        marker = public_demo.set(True)
        try:
            async for item in stream_agent(TASKS[task], max_attempts=1):
                # No retrieval, archive writes, run IDs or other visitors' data.
                if item['event'] == 'complete':
                    item['data']['result']['public_demo'] = True
                messages.put_nowait(item)
        except AgentResponseError:
            messages.put_nowait({'event': 'error', 'data': {'error': 'demo_provider_unavailable'}})
        except Exception:
            messages.put_nowait({'event': 'error', 'data': {'error': 'demo_unavailable'}})
        finally:
            public_demo.reset(marker)
    try:
        asyncio.run(run())
    finally:
        # A disconnected browser does not free the slot while work still runs.
        _release(ticket)
        messages.put_nowait(None)


@router.post('/stream')
async def demo_stream(body: DemoRequest, request: Request):
    _enabled()
    if body.task not in TASKS:
        raise HTTPException(422, 'Choose one of the demo examples')
    try:
        ticket = _reserve(_visitor(request))
    except sqlite3.Error:
        raise HTTPException(503, 'Demo quota checks are unavailable. Please try later.') from None
    messages = queue.Queue(maxsize=8)
    worker = threading.Thread(target=_work, args=(body.task, ticket, messages), daemon=True)
    try:
        worker.start()
    except RuntimeError:
        _release(ticket)
        raise HTTPException(503, 'The demo is unavailable. Please try later.') from None

    async def events():
        yield 'event: started\ndata: {"status":"running"}\n\n'
        heartbeat = time.monotonic()
        while True:
            if await request.is_disconnected():
                return
            try:
                item = messages.get_nowait()
            except queue.Empty:
                if time.monotonic() - heartbeat >= 10:
                    yield ': keep-alive\n\n'
                    heartbeat = time.monotonic()
                await asyncio.sleep(.1)
                continue
            if item is None:
                return
            yield f"event: {item['event']}\ndata: {json.dumps(jsonable_encoder(item['data']))}\n\n"

    return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})
