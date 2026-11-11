"""Read-only search over an explicitly configured local corpus."""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.memory.vector_store import LocalIndex

router = APIRouter()


class ContextQuery(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10, strict=True)


@router.post('/context/search')
def search_context(body: ContextQuery):
    root = os.getenv('RAG_ROOT')
    if not root:
        raise HTTPException(status_code=503, detail='Local retrieval is not configured')
    try:
        index = LocalIndex.from_directory(root)
    except (OSError, ValueError):
        raise HTTPException(status_code=503, detail='The configured corpus is unavailable') from None
    return {'matches': index.search(body.query, body.top_k), 'stats': index.stats}
