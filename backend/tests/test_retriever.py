"""
Test Jalon 3 — Nœud Récupérateur.
Tests unitaires (mock DB) + tests d'intégration (DB réelle + embeddings).
Lance avec :
    pytest tests/test_retriever.py -v                   # unit + mock
    pytest tests/test_retriever.py -v -m integration    # DB réelle
    pytest tests/test_retriever.py -v -m slow           # DB + BGE-M3
"""
import numpy as np
import pytest
from unittest.mock import patch

from agents.retriever import _rerank
from shared.schemas import ClauseType, Jurisdiction


# ---------------------------------------------------------------------------
# Données fixtures
# ---------------------------------------------------------------------------

def _make_articles(n: int = 10) -> list[dict]:
    return [
        {
            "id": f"MAURITANIA_LABOR-CODE_TRAVAIL_MR-{i + 1}",
            "jurisdiction": "mauritania_labor",
            "code_name": "CODE_TRAVAIL_MR",
            "article_number": str(i + 1),
            "hierarchy_path": "Dispositions générales",
            "full_text": f"Article {i + 1} : texte de test numéro {i}.",
            "language": "fr",
            "score": float(0.9 - i * 0.05),
            "text": f"Article {i + 1} : texte de test numéro {i}.",
        }
        for i in range(n)
    ]


def _make_clause(
    clause_id: str = "c001",
    type_clause: str = ClauseType.PERIODE_ESSAI.value,
    text: str = "période d'essai six mois maximum travailleur",
) -> dict:
    return {
        "clause_id": clause_id,
        "type_clause": type_clause,
        "text": text,
        "jurisdiction_hint": Jurisdiction.MAURITANIA_LABOR.value,
    }


# ---------------------------------------------------------------------------
# Tests _rerank
# ---------------------------------------------------------------------------

def test_rerank_returns_at_most_top_k():
    articles = _make_articles(10)
    result = _rerank("période essai travailleur", articles, top_k=5)
    assert len(result) <= 5


def test_rerank_fallback_when_no_reranker():
    articles = _make_articles(10)
    with patch("agents.retriever._load_reranker", return_value=None):
        result = _rerank("période essai", articles, top_k=3)
    assert len(result) == 3
    assert result[0]["id"] == articles[0]["id"]


def test_rerank_empty_candidates():
    result = _rerank("query", [], top_k=5)
    assert result == []


def test_rerank_fewer_than_top_k():
    articles = _make_articles(3)
    result = _rerank("query", articles, top_k=5)
    assert len(result) == 3


# ---------------------------------------------------------------------------
# Tests retriever_node avec mocks
# ---------------------------------------------------------------------------

def test_retriever_node_empty_clauses():
    from agents.retriever import retriever_node
    state = {
        "clauses": [],
        "jurisdiction": "mauritania_labor",
        "contract_id": "t",
        "contract_text": "",
        "extracted": {},
        "retrievals": {},
        "findings": [],
        "errors": [],
    }
    result = retriever_node(state)
    assert result["retrievals"] == {}


def test_retriever_node_with_mock_search():
    """Test retriever_node avec embed_query et search_articles mockés."""
    from agents.retriever import retriever_node

    mock_embedding = np.random.rand(1024).astype(np.float32)
    mock_embedding /= np.linalg.norm(mock_embedding)
    mock_articles = _make_articles(5)

    with patch("agents.retriever.embed_query", return_value=mock_embedding), \
         patch("agents.retriever.search_articles", return_value=mock_articles):
        state = {
            "clauses": [_make_clause("clause-1"), _make_clause("clause-2")],
            "jurisdiction": "mauritania_labor",
            "contract_id": "t",
            "contract_text": "",
            "extracted": {},
            "retrievals": {},
            "findings": [],
            "errors": [],
        }
        result = retriever_node(state)

    assert "clause-1" in result["retrievals"]
    assert "clause-2" in result["retrievals"]


def test_retriever_node_adds_text_key():
    """Vérifie que 'text' est ajouté comme alias de full_text."""
    from agents.retriever import retriever_node

    mock_embedding = np.random.rand(1024).astype(np.float32)
    mock_embedding /= np.linalg.norm(mock_embedding)
    articles = [
        {
            "id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
            "jurisdiction": "mauritania_labor",
            "code_name": "CODE_TRAVAIL_MR",
            "article_number": "10",
            "hierarchy_path": None,
            "full_text": "Article 10 : La période d'essai ne peut excéder six mois.",
            "language": "fr",
            "score": 0.95,
        }
    ]

    with patch("agents.retriever.embed_query", return_value=mock_embedding), \
         patch("agents.retriever.search_articles", return_value=articles):
        state = {
            "clauses": [_make_clause("c1")],
            "jurisdiction": "mauritania_labor",
            "contract_id": "t",
            "contract_text": "",
            "extracted": {},
            "retrievals": {},
            "findings": [],
            "errors": [],
        }
        result = retriever_node(state)

    arts = result["retrievals"]["c1"]
    assert all("text" in a for a in arts)
    assert "Article 10" in arts[0]["text"]


def test_retriever_node_handles_search_error():
    """En cas d'erreur de recherche, la clause retourne une liste vide."""
    from agents.retriever import retriever_node

    mock_embedding = np.random.rand(1024).astype(np.float32)

    with patch("agents.retriever.embed_query", return_value=mock_embedding), \
         patch("agents.retriever.search_articles", side_effect=RuntimeError("DB error")):
        state = {
            "clauses": [_make_clause("err-clause")],
            "jurisdiction": "mauritania_labor",
            "contract_id": "t",
            "contract_text": "",
            "extracted": {},
            "retrievals": {},
            "findings": [],
            "errors": [],
        }
        result = retriever_node(state)

    assert result["retrievals"]["err-clause"] == []


# ---------------------------------------------------------------------------
# Tests d'intégration — DB réelle + embeddings BGE-M3
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def seeded_db():
    """Insère les articles seed avec vrais embeddings."""
    from ingestion.embedder import embed_texts
    from ingestion.loader import insert_articles
    from ingestion.seed_articles import ALL_ARTICLES

    texts = [a.full_text for a in ALL_ARTICLES]
    embeddings = embed_texts(texts, batch_size=32, show_progress=False)
    insert_articles(ALL_ARTICLES, embeddings=embeddings)
    return True


@pytest.mark.slow
def test_retriever_finds_art10_for_essai_query(seeded_db):
    """Critère PDF : requête période essai → Art.10 CODE_TRAVAIL_MR dans top-5."""
    from agents.retriever import retriever_node

    clause = _make_clause(
        clause_id="essai-clause",
        text="période d'essai six mois maximum travailleur",
    )
    state = {
        "clauses": [clause],
        "jurisdiction": "mauritania_labor",
        "contract_id": "t",
        "contract_text": "",
        "extracted": {},
        "retrievals": {},
        "findings": [],
        "errors": [],
    }
    result = retriever_node(state)
    ids = [a["id"] for a in result["retrievals"]["essai-clause"]]
    assert "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10" in ids, (
        f"Art.10 absent du top-5. Obtenu: {ids}"
    )


@pytest.mark.slow
def test_retriever_top5_limit(seeded_db):
    """Le récupérateur retourne au plus 5 articles par clause."""
    from agents.retriever import retriever_node

    state = {
        "clauses": [_make_clause("c1", text="contrat de travail emploi")],
        "jurisdiction": "mauritania_labor",
        "contract_id": "t",
        "contract_text": "",
        "extracted": {},
        "retrievals": {},
        "findings": [],
        "errors": [],
    }
    result = retriever_node(state)
    assert len(result["retrievals"]["c1"]) <= 5


@pytest.mark.slow
def test_retriever_labor_jurisdiction(seeded_db):
    """Le filtrage par juridiction mauritania_labor fonctionne."""
    from agents.retriever import retriever_node

    state = {
        "clauses": [_make_clause("cl", text="période essai travailleur 6 mois")],
        "jurisdiction": "mauritania_labor",
        "contract_id": "t",
        "contract_text": "",
        "extracted": {},
        "retrievals": {},
        "findings": [],
        "errors": [],
    }
    result = retriever_node(state)
    arts = result["retrievals"]["cl"]
    assert all(a["jurisdiction"] == "mauritania_labor" for a in arts), (
        f"Articles d'une autre juridiction dans les résultats: {[a['id'] for a in arts]}"
    )
