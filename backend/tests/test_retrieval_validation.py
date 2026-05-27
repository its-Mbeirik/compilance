"""
Test Jalon 2 — Validation critique : critère Go/No-Go PDF.
"La requête 'capital minimum SARL' retourne l'article 311 AUSCGIE en top-3
sur 10 essais." (section 4.3 du PDF)

Lance avec : pytest tests/test_retrieval_validation.py -v -m slow
Prérequis : docker compose up -d + sentence-transformers installé
"""
import pytest
import numpy as np

from ingestion.embedder import embed_query, embed_texts
from ingestion.loader import insert_articles, search_articles
from ingestion.seed_articles import ALL_ARTICLES


@pytest.fixture(scope="module")
def seeded_db_with_real_embeddings():
    """Insère les articles seed avec de vrais embeddings BGE-M3."""
    texts = [a.full_text for a in ALL_ARTICLES]
    embeddings = embed_texts(texts, batch_size=32, show_progress=False)
    insert_articles(ALL_ARTICLES, embeddings=embeddings)
    return True


# ---------------------------------------------------------------------------
# Critère Go/No-Go Jalon 2 — requête "capital minimum SARL" → Art.311 top-3
# ---------------------------------------------------------------------------

QUERIES_ART311 = [
    "capital minimum SARL",
    "capital social minimum d'une SARL",
    "montant minimum du capital pour une SARL",
    "capital social SARL 1 000 000 FCFA",
    "SARL capital inférieur à un million de francs CFA",
    "capital social SARL OHADA",
    "montant du capital social SARL associés statuts",
    "SARL capital minimum francs CFA obligation",
    "capital SARL librement fixé associés minimum",
    "seuil capital SARL Acte Uniforme",
]


@pytest.mark.slow
def test_art311_in_top3_all_10_queries(seeded_db_with_real_embeddings):
    """
    Critère PDF section 4.3 :
    'requête capital minimum SARL retourne Art. 311 AUSCGIE en top-3 sur 10 essais'
    """
    failures = []
    for query in QUERIES_ART311:
        q_emb = embed_query(query)
        results = search_articles(q_emb, jurisdiction="ohada", top_k=3)
        ids = [r["id"] for r in results]
        if "OHADA-AUSCGIE-311" not in ids:
            top5 = search_articles(q_emb, jurisdiction="ohada", top_k=5)
            failures.append({
                "query": query,
                "top3": ids,
                "top5": [r["id"] for r in top5],
                "scores": [r["score"] for r in results],
            })

    assert not failures, (
        f"Art.311 absent du top-3 sur {len(failures)}/10 requêtes:\n"
        + "\n".join(
            f"  '{f['query']}' → top3={f['top3']} | top5={f['top5']}"
            for f in failures
        )
    )


@pytest.mark.slow
def test_art311_in_top5_relaxed(seeded_db_with_real_embeddings):
    """Test de robustesse avec seuil relaxé à top-5 (aucun échec toléré)."""
    failures = []
    for query in QUERIES_ART311:
        q_emb = embed_query(query)
        results = search_articles(q_emb, jurisdiction="ohada", top_k=5)
        ids = [r["id"] for r in results]
        if "OHADA-AUSCGIE-311" not in ids:
            failures.append(query)

    assert not failures, (
        f"Art.311 absent du top-5 sur les requêtes : {failures}"
    )


# ---------------------------------------------------------------------------
# Tests de validation supplémentaires — règles des sections 5.3.1 et 5.3.2
# ---------------------------------------------------------------------------

VALIDATION_QUERIES = [
    # (query, expected_article_id, top_k)
    ("durée maximale société 99 ans",          "OHADA-AUSCGIE-28",         5),
    ("siège social boîte postale interdit",    "OHADA-AUSCGIE-25",         5),
    ("capital société anonyme SA minimum",     "OHADA-AUSCGIE-387",        5),
    ("libération capital SA quart souscription", "OHADA-AUSCGIE-389",      5),
    ("mentions obligatoires statuts société",  "OHADA-AUSCGIE-13",         5),
    ("période d'essai maximum six mois",       "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10", 5),
    ("CDD plus trois mois visa inspection",    "MAURITANIA_LABOR-CODE_TRAVAIL_MR-18", 5),
    ("âge minimum travail quatorze ans",       "MAURITANIA_LABOR-CODE_TRAVAIL_MR-153", 5),
    ("congés payés douze mois travail",        "MAURITANIA_LABOR-CODE_TRAVAIL_MR-178", 5),
    ("contrat de travail définition employeur", "MAURITANIA_LABOR-CODE_TRAVAIL_MR-4",  5),
]


@pytest.mark.slow
def test_validation_rules_top5(seeded_db_with_real_embeddings):
    """
    Vérifie que les 10 règles cibles des sections 5.3.1 et 5.3.2 du PDF
    sont retrouvées dans le top-5 (Recall@5 ≥ 0.80 attendu, cible 0.90).
    """
    found = 0
    failed = []

    for query, expected_id, top_k in VALIDATION_QUERIES:
        q_emb = embed_query(query)
        results = search_articles(
            q_emb,
            jurisdiction=expected_id.split("-")[0].lower() if "OHADA" in expected_id else "mauritania_labor",
            top_k=top_k,
        )
        ids = [r["id"] for r in results]
        if expected_id in ids:
            found += 1
        else:
            failed.append((query, expected_id, ids[:3]))

    recall_at_5 = found / len(VALIDATION_QUERIES)
    print(f"\nRecall@5 sur règles cibles: {recall_at_5:.2f} ({found}/{len(VALIDATION_QUERIES)})")

    if failed:
        print("Règles non retrouvées:")
        for q, exp, got in failed:
            print(f"  '{q}' → attendu {exp}, obtenu {got}")

    assert recall_at_5 >= 0.80, (
        f"Recall@5 = {recall_at_5:.2f} < seuil minimal 0.80 (PDF Tab.4)"
    )
