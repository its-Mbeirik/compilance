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
from unittest.mock import MagicMock, patch

from agents.retriever import _rerank
from shared.schemas import ClauseType, Jurisdiction


# ---------------------------------------------------------------------------
# Données fixtures
# ---------------------------------------------------------------------------

def _make_articles(n: int = 10) -> list[dict]:
    return [
        {
            "id": f"OHADA-AUSCGIE-{300 + i}",
            "jurisdiction": "ohada",
            "code_name": "AUSCGIE",
            "article_number": str(300 + i),
            "hierarchy_path": "Livre 2",
            "full_text": f"Article {300 + i} : texte de test numéro {i}.",
            "language": "fr",
            "score": float(0.9 - i * 0.05),
            "text": f"Article {300 + i} : texte de test numéro {i}.",
        }
        for i in range(n)
    ]


def _make_clause(
    clause_id: str = "c001",
    type_clause: str = ClauseType.CAPITAL_SOCIAL.value,
    text: str = "capital social SARL 1 000 000 FCFA",
) -> dict:
    return {
        "clause_id": clause_id,
        "type_clause": type_clause,
        "text": text,
        "jurisdiction_hint": Jurisdiction.OHADA.value,
    }


# ---------------------------------------------------------------------------
# Tests _rerank
# ---------------------------------------------------------------------------

def test_rerank_returns_at_most_top_k():
    articles = _make_articles(10)
    result = _rerank("capital social SARL", articles, top_k=5)
    assert len(result) <= 5


def test_rerank_fallback_when_no_reranker():
    articles = _make_articles(10)
    with patch("agents.retriever._load_reranker", return_value=None):
        result = _rerank("capital social", articles, top_k=3)
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
        "jurisdiction": "ohada",
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
            "jurisdiction": "ohada",
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
            "id": "OHADA-AUSCGIE-311",
            "jurisdiction": "ohada",
            "code_name": "AUSCGIE",
            "article_number": "311",
            "hierarchy_path": None,
            "full_text": "Article 311 : capital minimum 1 000 000 FCFA.",
            "language": "fr",
            "score": 0.95,
        }
    ]

    with patch("agents.retriever.embed_query", return_value=mock_embedding), \
         patch("agents.retriever.search_articles", return_value=articles):
        state = {
            "clauses": [_make_clause("c1")],
            "jurisdiction": "ohada",
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
    assert arts[0]["text"] == "Article 311 : capital minimum 1 000 000 FCFA."


def test_retriever_node_handles_search_error():
    """En cas d'erreur de recherche, la clause retourne une liste vide."""
    from agents.retriever import retriever_node

    mock_embedding = np.random.rand(1024).astype(np.float32)

    with patch("agents.retriever.embed_query", return_value=mock_embedding), \
         patch("agents.retriever.search_articles", side_effect=RuntimeError("DB error")):
        state = {
            "clauses": [_make_clause("err-clause")],
            "jurisdiction": "ohada",
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
def test_retriever_finds_art311_for_capital_query(seeded_db):
    """Critère PDF : requête capital SARL → Art.311 dans top-5."""
    from agents.retriever import retriever_node

    clause = _make_clause(
        clause_id="cap-clause",
        text="capital social SARL 500 000 FCFA minimum",
    )
    state = {
        "clauses": [clause],
        "jurisdiction": "ohada",
        "contract_id": "t",
        "contract_text": "",
        "extracted": {},
        "retrievals": {},
        "findings": [],
        "errors": [],
    }
    result = retriever_node(state)
    ids = [a["id"] for a in result["retrievals"]["cap-clause"]]
    assert "OHADA-AUSCGIE-311" in ids, (
        f"Art.311 absent du top-5. Obtenu: {ids}"
    )


@pytest.mark.slow
def test_retriever_top5_limit(seeded_db):
    """Le récupérateur retourne au plus 5 articles par clause."""
    from agents.retriever import retriever_node

    state = {
        "clauses": [_make_clause("c1", text="capital social société")],
        "jurisdiction": "ohada",
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
    """Le filtrage par juridiction fonctionne."""
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
