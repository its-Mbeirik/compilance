"""
Test Jalon 2 — Ingestion DB : seed articles sans embeddings + avec embeddings factices.
Lance avec : pytest tests/test_ingestion_db.py -v -m integration
Prérequis : docker compose up -d
"""
import numpy as np
import pytest

from ingestion.loader import count_articles, insert_articles, search_articles
from ingestion.seed_articles import AUSCGIE_ARTICLES, CODE_TRAVAIL_ARTICLES, ALL_ARTICLES


@pytest.mark.integration
def test_seed_insert_without_embeddings():
    """Insère tous les articles seed sans embedding — vérifie le count."""
    before = count_articles()
    inserted = insert_articles(ALL_ARTICLES, embeddings=None)
    after = count_articles()
    assert inserted == len(ALL_ARTICLES)
    assert after >= len(ALL_ARTICLES)


@pytest.mark.integration
def test_seed_insert_ohada_count():
    insert_articles(AUSCGIE_ARTICLES, embeddings=None)
    n = count_articles("ohada")
    assert n >= len(AUSCGIE_ARTICLES), (
        f"Attendu >= {len(AUSCGIE_ARTICLES)} articles OHADA, obtenu {n}"
    )


@pytest.mark.integration
def test_seed_insert_labor_count():
    insert_articles(CODE_TRAVAIL_ARTICLES, embeddings=None)
    n = count_articles("mauritania_labor")
    assert n >= len(CODE_TRAVAIL_ARTICLES), (
        f"Attendu >= {len(CODE_TRAVAIL_ARTICLES)} articles labour, obtenu {n}"
    )


@pytest.mark.integration
def test_seed_upsert_idempotent():
    """Deux insertions successives ne doublent pas les articles."""
    insert_articles(ALL_ARTICLES, embeddings=None)
    count1 = count_articles()
    insert_articles(ALL_ARTICLES, embeddings=None)
    count2 = count_articles()
    assert count1 == count2, "L'upsert ne doit pas créer de doublons"


@pytest.mark.integration
def test_insert_with_fake_embeddings():
    """Insère avec des embeddings aléatoires normalisés (dim 1024)."""
    n = len(ALL_ARTICLES)
    fake_embs = np.random.rand(n, 1024).astype(np.float32)
    norms = np.linalg.norm(fake_embs, axis=1, keepdims=True)
    fake_embs = fake_embs / norms

    inserted = insert_articles(ALL_ARTICLES, embeddings=fake_embs)
    assert inserted == n


@pytest.mark.integration
def test_search_returns_results_with_embeddings():
    """Vérifie que search_articles fonctionne avec des embeddings présents."""
    # S'assure qu'il y a au moins un article avec embedding
    n = len(ALL_ARTICLES)
    fake_embs = np.random.rand(n, 1024).astype(np.float32)
    fake_embs /= np.linalg.norm(fake_embs, axis=1, keepdims=True)
    insert_articles(ALL_ARTICLES, embeddings=fake_embs)

    query_emb = np.random.rand(1024).astype(np.float32)
    query_emb /= np.linalg.norm(query_emb)

    results = search_articles(query_emb, jurisdiction="ohada", top_k=5)
    assert len(results) > 0
    assert all("id" in r for r in results)
    assert all("score" in r for r in results)
    assert all("full_text" in r for r in results)


@pytest.mark.integration
def test_search_scores_between_minus1_and_1():
    """Les scores cosinus doivent être dans [-1, 1]."""
    query_emb = np.random.rand(1024).astype(np.float32)
    query_emb /= np.linalg.norm(query_emb)
    results = search_articles(query_emb, top_k=10)
    for r in results:
        assert -1.01 <= r["score"] <= 1.01, f"Score hors bornes: {r['score']}"


@pytest.mark.integration
def test_search_filtered_by_jurisdiction():
    """La recherche filtrée par juridiction ne retourne que des articles de cette juridiction."""
    query_emb = np.random.rand(1024).astype(np.float32)
    query_emb /= np.linalg.norm(query_emb)

    ohada_results = search_articles(query_emb, jurisdiction="ohada", top_k=10)
    labor_results = search_articles(query_emb, jurisdiction="mauritania_labor", top_k=10)

    assert all(r["jurisdiction"] == "ohada" for r in ohada_results)
    assert all(r["jurisdiction"] == "mauritania_labor" for r in labor_results)
