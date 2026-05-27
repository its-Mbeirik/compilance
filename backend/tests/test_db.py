"""
Test Jalon 1 — Connexion PostgreSQL + pgvector.
Critère PDF : extension vector chargée, tables legal_articles/contracts/analyses créées.
Lance avec : pytest tests/test_db.py -v -m integration
Prérequis : docker compose up -d
"""
import pytest
from db.database import check_pgvector, check_tables, get_connection


@pytest.mark.integration
def test_pgvector_extension_loaded():
    assert check_pgvector(), "Extension pgvector (vector) non chargée dans PostgreSQL"


@pytest.mark.integration
def test_tables_exist():
    tables = check_tables()
    assert "legal_articles" in tables, f"Table legal_articles absente. Tables: {tables}"
    assert "contracts" in tables, f"Table contracts absente."
    assert "analyses" in tables, f"Table analyses absente."


@pytest.mark.integration
def test_hnsw_index_exists():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'legal_articles' AND indexname = 'articles_hnsw_idx'"
            )
            row = cur.fetchone()
    assert row is not None, "Index HNSW 'articles_hnsw_idx' absent"


@pytest.mark.integration
def test_insert_and_query_article():
    """Vérifie qu'on peut insérer un article sans embedding et le relire."""
    import uuid
    test_id = f"TEST-{uuid.uuid4().hex[:8]}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO legal_articles
                    (id, jurisdiction, code_name, article_number, full_text, language)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (test_id, "test", "TEST_CODE", "0", "Texte de test.", "fr"),
            )
            cur.execute("SELECT id FROM legal_articles WHERE id = %s", (test_id,))
            row = cur.fetchone()
            # Nettoyage
            cur.execute("DELETE FROM legal_articles WHERE id = %s", (test_id,))
    assert row is not None
    assert row[0] == test_id


@pytest.mark.integration
def test_vector_insert_and_cosine():
    """Insère un vecteur factice dim=1024 et vérifie la recherche cosinus."""
    import uuid
    import numpy as np

    test_id = f"TEST-VEC-{uuid.uuid4().hex[:8]}"
    vec = np.random.rand(1024).astype(np.float32)
    vec /= np.linalg.norm(vec)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO legal_articles
                    (id, jurisdiction, code_name, article_number, full_text, language, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (test_id, "test", "TEST", "0", "Vecteur test.", "fr", vec),
            )
            cur.execute(
                "SELECT id, 1 - (embedding <=> %s::vector) AS cosine "
                "FROM legal_articles WHERE id = %s",
                (vec, test_id),
            )
            row = cur.fetchone()
            cur.execute("DELETE FROM legal_articles WHERE id = %s", (test_id,))

    assert row is not None
    cosine_score = row[1]
    assert cosine_score > 0.999, f"Cosine self-similarity trop faible: {cosine_score}"
