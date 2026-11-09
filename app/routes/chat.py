import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest
from app.services.llm.structured import AgentResponseError
from app.agents.manager import run_agent, stream_agent

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest):
    try:
        return run_agent(request.prompt)
    except AgentResponseError as error:
        raise HTTPException(
            status_code=502,
            detail={"error": error.kind, "stage": error.stage},
        ) from error

@router.post('/chat/stream')
async def chat_stream(body: ChatRequest, request: Request):
    async def events():
        index = 0

        def encode(event, data):
            nonlocal index
            index += 1
            payload = json.dumps(jsonable_encoder(data), ensure_ascii=False)
            return f'id: {index}\nevent: {event}\ndata: {payload}\n\n'

        yield encode('started', {'status': 'running'})
        try:
            async for item in stream_agent(body.prompt, cancelled=request.is_disconnected):
                yield encode(item['event'], item['data'])
        except AgentResponseError as error:
            yield encode('error', {'error': error.kind, 'stage': error.stage})
        except Exception:
            # Headers are already sent: stream errors must be terminal SSE events.
            yield encode('error', {'error': 'internal_error'})

    return StreamingResponse(events(), media_type='text/event-stream', headers={
        'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no',
    })
