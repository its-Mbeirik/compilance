"""Matching agent.

For each extracted clause, retrieves the most relevant legal passages from
pgvector. The query is built from the clause's topic + a snippet of its text,
which works well with the bge-m3 multilingual embeddings.
"""

from __future__ import annotations

import logging

from app.agents.state import ConformityState
from app.rag.retriever import retrieve

logger = logging.getLogger(__name__)


def matching_node(state: ConformityState) -> ConformityState:
    clauses = state.get("clauses", [])
    retrievals: dict[str, list[dict]] = {}

    for clause in clauses:
        query = f"{clause.topic} {clause.title} {clause.text[:400]}".strip()
        try:
            hits = retrieve(query, k=5)
        except Exception as e:
            logger.exception("Retrieval failed for %s: %s", clause.ref, e)
            hits = []
        retrievals[clause.ref] = [
            {
                "source": h.source_title,
                "article": h.article_ref,
                "excerpt": h.content[:800],
                "score": round(h.score, 4),
            }
            for h in hits
        ]

    logger.info("Matching done: %d clauses -> %d retrievals", len(clauses), sum(len(v) for v in retrievals.values()))
    return {"retrievals": retrievals}
