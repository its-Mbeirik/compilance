"""
Jalon 3 — Nœud Récupérateur.
Pour chaque clause : BGE-M3 embed → pgvector top-25 → BGE-reranker-v2-m3 → top-5.
Le reranker est optionnel ; si FlagEmbedding n'est pas installé on garde le top-5 cosinus.
"""
import logging
from typing import Any

import numpy as np

from ingestion.embedder import embed_query
from ingestion.loader import search_articles
from shared.schemas import AgentState

logger = logging.getLogger(__name__)

_RERANKER = None  # singleton


def _load_reranker(model_name: str = "BAAI/bge-reranker-v2-m3"):
    global _RERANKER
    if _RERANKER is not None:
        return _RERANKER
    try:
        from FlagEmbedding import FlagReranker
        logger.info(f"Chargement reranker {model_name} ...")
        _RERANKER = FlagReranker(model_name, use_fp16=True)
        logger.info("Reranker chargé.")
    except ImportError:
        logger.warning(
            "FlagEmbedding non installé — reranker désactivé, fallback cosinus top-5."
        )
        _RERANKER = None
    return _RERANKER


def _rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Réordonne les candidats avec BGE-reranker-v2-m3.
    Si le reranker n'est pas disponible, retourne les top_k premiers par score cosinus.
    """
    reranker = _load_reranker()

    if reranker is None or not candidates:
        return candidates[:top_k]

    pairs = [[query, c["full_text"]] for c in candidates]
    try:
        scores = reranker.compute_score(pairs, normalize=True)
        if not isinstance(scores, list):
            scores = scores.tolist()
        ranked = sorted(
            zip(scores, candidates),
            key=lambda x: x[0],
            reverse=True,
        )
        results = []
        for score, art in ranked[:top_k]:
            art = dict(art)
            art["rerank_score"] = float(score)
            results.append(art)
        return results
    except Exception as exc:
        logger.warning(f"Reranker error ({exc}), fallback cosinus.")
        return candidates[:top_k]


def retriever_node(state: AgentState) -> dict[str, Any]:
    """
    Nœud Récupérateur :
    - Pour chaque clause dans state['clauses']
    - Embed la requête avec BGE-M3
    - Recherche pgvector top-25 (filtré par juridiction)
    - Rerank → top-5
    - Ajoute 'text' = full_text pour la garde-fou de citation
    """
    clauses: list[dict] = state.get("clauses", [])
    jurisdiction: str = state["jurisdiction"]
    retrievals: dict[str, list[dict]] = {}

    if not clauses:
        logger.warning("Récupérateur: aucune clause à traiter.")
        return {"retrievals": {}}

    for clause in clauses:
        clause_id: str = clause["clause_id"]
        query_text: str = clause["text"]

        try:
            q_emb: np.ndarray = embed_query(query_text)
            top_25 = search_articles(q_emb, jurisdiction=jurisdiction, top_k=25)

            if not top_25:
                logger.warning(f"Aucun article trouvé pour clause '{clause_id}' ({query_text!r})")
                retrievals[clause_id] = []
                continue

            top_5 = _rerank(query_text, top_25, top_k=5)

            # Normalise : ajoute 'text' (alias de full_text) pour citation_guard
            for art in top_5:
                art.setdefault("text", art.get("full_text", ""))

            retrievals[clause_id] = top_5
            logger.debug(
                f"Clause '{clause_id}': top-1 = {top_5[0]['id']} "
                f"(score={top_5[0].get('rerank_score', top_5[0].get('score', '?')):.3f})"
                if top_5 else f"Clause '{clause_id}': aucun résultat"
            )

        except Exception as exc:
            logger.error(f"Erreur Récupérateur clause '{clause_id}': {exc}")
            retrievals[clause_id] = []

    logger.info(f"Récupérateur: {len(retrievals)} clauses traitées.")
    return {"retrievals": retrievals}
