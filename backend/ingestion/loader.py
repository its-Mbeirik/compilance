"""
Jalon 2 — Insertion des articles dans PostgreSQL + pgvector.
Upsert sur conflict (id) pour permettre les ré-ingestions.
"""
import json
import logging
from typing import Optional

import numpy as np

from db.database import get_connection
from ingestion.parser import RawArticle

logger = logging.getLogger(__name__)


def insert_articles(
    articles: list[RawArticle],
    embeddings: Optional[np.ndarray] = None,
) -> int:
    """
    Insère (ou met à jour) les articles dans la table legal_articles.

    Args:
        articles:   liste de RawArticle
        embeddings: array (N, 1024) aligné sur articles. None → colonne vide.

    Returns:
        Nombre d'articles réellement insérés/mis à jour.
    """
    if embeddings is not None:
        assert len(embeddings) == len(articles), (
            f"Mismatch : {len(articles)} articles mais {len(embeddings)} embeddings"
        )

    inserted = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for i, article in enumerate(articles):
                emb = embeddings[i].tolist() if embeddings is not None else None
                override_json = json.dumps(article.country_override)

                cur.execute(
                    """
                    INSERT INTO legal_articles
                        (id, jurisdiction, code_name, article_number,
                         hierarchy_path, full_text, language,
                         version_date, country_override, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        full_text        = EXCLUDED.full_text,
                        hierarchy_path   = EXCLUDED.hierarchy_path,
                        embedding        = EXCLUDED.embedding,
                        version_date     = EXCLUDED.version_date,
                        country_override = EXCLUDED.country_override
                    """,
                    (
                        article.id,
                        article.jurisdiction,
                        article.code_name,
                        article.article_number,
                        article.hierarchy_path,
                        article.full_text,
                        article.language,
                        article.version_date,
                        override_json,
                        emb,
                    ),
                )
                inserted += 1

    logger.info(f"{inserted} articles insérés/mis à jour dans legal_articles.")
    return inserted


def count_articles(jurisdiction: Optional[str] = None) -> int:
    """Retourne le nombre d'articles indexés (optionnellement filtrés par juridiction)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if jurisdiction:
                cur.execute(
                    "SELECT COUNT(*) FROM legal_articles WHERE jurisdiction = %s",
                    (jurisdiction,),
                )
            else:
                cur.execute("SELECT COUNT(*) FROM legal_articles")
            return cur.fetchone()[0]


def search_articles(
    query_embedding: np.ndarray,
    jurisdiction: Optional[str] = None,
    top_k: int = 25,
) -> list[dict]:
    """
    Recherche cosinus dans pgvector.
    Retourne les top_k articles les plus proches, avec score.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if jurisdiction:
                cur.execute(
                    """
                    SELECT id, jurisdiction, code_name, article_number,
                           hierarchy_path, full_text, language,
                           1 - (embedding <=> %s::vector) AS score
                    FROM legal_articles
                    WHERE jurisdiction = %s
                      AND embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_embedding.tolist(), jurisdiction,
                     query_embedding.tolist(), top_k),
                )
            else:
                cur.execute(
                    """
                    SELECT id, jurisdiction, code_name, article_number,
                           hierarchy_path, full_text, language,
                           1 - (embedding <=> %s::vector) AS score
                    FROM legal_articles
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_embedding.tolist(), query_embedding.tolist(), top_k),
                )

            rows = cur.fetchall()

    return [
        {
            "id": r[0], "jurisdiction": r[1], "code_name": r[2],
            "article_number": r[3], "hierarchy_path": r[4],
            "full_text": r[5], "language": r[6], "score": float(r[7]),
        }
        for r in rows
    ]
