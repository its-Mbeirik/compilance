"""Vector retrieval from `legal_chunks` using cosine similarity on pgvector."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.db.models import LegalChunk
from app.db.session import session_scope
from app.rag.embeddings import embed_query


@dataclass
class RetrievedChunk:
    id: str
    source_file: str
    source_title: str
    article_ref: str | None
    content: str
    score: float


def retrieve(query: str, k: int = 6) -> list[RetrievedChunk]:
    """Top-k nearest legal chunks for `query` (cosine distance)."""
    query_vec = embed_query(query)
    with session_scope() as db:
        stmt = (
            select(LegalChunk, LegalChunk.embedding.cosine_distance(query_vec).label("distance"))
            .order_by("distance")
            .limit(k)
        )
        rows = db.execute(stmt).all()

    return [
        RetrievedChunk(
            id=row.LegalChunk.id,
            source_file=row.LegalChunk.source_file,
            source_title=row.LegalChunk.source_title,
            article_ref=row.LegalChunk.article_ref,
            content=row.LegalChunk.content,
            score=1.0 - float(row.distance),
        )
        for row in rows
    ]


def format_for_prompt(chunks: list[RetrievedChunk]) -> str:
    """Render retrieved chunks for inclusion in an LLM prompt with citation tags."""
    if not chunks:
        return "[Aucun extrait juridique pertinent trouvé]"
    parts = []
    for i, c in enumerate(chunks, 1):
        ref = c.article_ref or "passage"
        parts.append(
            f"[Source {i}: {c.source_title} — {ref}]\n{c.content}\n"
        )
    return "\n---\n".join(parts)
