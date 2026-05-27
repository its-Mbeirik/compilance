"""Endpoints for inspecting the legal corpus."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import LegalChunk
from app.db.session import get_db
from app.rag.retriever import retrieve

router = APIRouter(prefix="/corpus", tags=["corpus"])


class CorpusStats(BaseModel):
    total_chunks: int
    sources: list[dict]


@router.get("/stats", response_model=CorpusStats)
def stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(LegalChunk.id))) or 0
    rows = db.execute(
        select(LegalChunk.source_file, func.count(LegalChunk.id))
        .group_by(LegalChunk.source_file)
        .order_by(LegalChunk.source_file)
    ).all()
    return CorpusStats(
        total_chunks=total,
        sources=[{"file": r[0], "chunks": r[1]} for r in rows],
    )


@router.get("/search")
def search(q: str, k: int = 5):
    hits = retrieve(q, k=k)
    return [
        {
            "source": h.source_title,
            "article": h.article_ref,
            "score": round(h.score, 4),
            "content": h.content,
        }
        for h in hits
    ]
