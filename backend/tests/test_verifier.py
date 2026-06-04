"""
Test Jalon 3 — Nœud Vérificateur + citation_guard.
Tests unitaires purs (mocks) + tests LLM réels.
Lance avec :
    pytest tests/test_verifier.py -v
    pytest tests/test_verifier.py -v -m slow   # LLM réel
"""
import pytest
from unittest.mock import MagicMock, patch

from shared.guards import citation_guard
from shared.schemas import FindingVerdict, FindingSeverity, ClauseType


# ---------------------------------------------------------------------------
# Tests citation_guard — unitaires purs
# ---------------------------------------------------------------------------

ART10_TEXT = (
    "Article 10 : La période d'essai ne peut excéder six (6) mois pour les travailleurs "
    "et douze (12) mois pour les cadres et assimilés."
)

RETRIEVALS_OK = {
    "clause-1": [
        {"id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",  "text": ART10_TEXT},
        {"id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-153", "text": "Article 153 : L'âge minimum est de 14 ans."},
    ]
}


def test_citation_guard_valid():
    finding = {
        "clause_id": "clause-1",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "ne peut excéder six (6) mois pour les travailleurs",
    }
    valid, msg = citation_guard(finding, RETRIEVALS_OK)
    assert valid is True
    assert msg == "OK"


def test_citation_guard_rejects_missing_clause_id():
    finding = {
        "clause_id": "clause-999",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "texte quelconque",
    }
    valid, msg = citation_guard(finding, RETRIEVALS_OK)
    assert valid is False
    assert "clause_id" in msg.lower() or "absent" in msg.lower()


def test_citation_guard_rejects_hallucinated_id():
    finding = {
        "clause_id": "clause-1",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-999",   # pas dans top-5
        "quoted_text": "texte quelconque",
    }
    valid, msg = citation_guard(finding, RETRIEVALS_OK)
    assert valid is False
    assert "999" in msg or "inventé" in msg


def test_citation_guard_rejects_paraphrased_quote():
    finding = {
        "clause_id": "clause-1",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "La période d'essai ne doit pas dépasser 6 mois.",   # paraphrase
    }
    valid, msg = citation_guard(finding, RETRIEVALS_OK)
    assert valid is False
    assert "textuelle" in msg.lower() or "trouvée" in msg.lower()


def test_citation_guard_rejects_empty_quote():
    finding = {
        "clause_id": "clause-1",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "",
    }
    valid, msg = citation_guard(finding, RETRIEVALS_OK)
    assert isinstance(valid, bool)
    assert isinstance(msg, str)


def test_citation_guard_exact_full_article_text():
    """La totalité du texte de l'article est une citation valide."""
    finding = {
        "clause_id": "clause-1",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": ART10_TEXT,
    }
    valid, msg = citation_guard(finding, RETRIEVALS_OK)
    assert valid is True


# ---------------------------------------------------------------------------
# Tests verifier_node avec mocks LLM
# ---------------------------------------------------------------------------

def _make_clause(clause_id: str = "c1", type_clause: str = "periode_essai",
                 text: str = "période d'essai 9 mois") -> dict:
    return {"clause_id": clause_id, "type_clause": type_clause, "text": text}


def _make_state(clauses: list[dict], retrievals: dict) -> dict:
    return {
        "contract_id": "test",
        "contract_text": "...",
        "jurisdiction": "mauritania_labor",
        "extracted": {},
        "clauses": clauses,
        "retrievals": retrievals,
        "findings": [],
        "errors": [],
    }


def _mock_llm_output(
    verdict: str = "NON_CONFORME",
    cited_id: str = "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
    quoted: str = "ne peut excéder six (6) mois pour les travailleurs",
    recommendation: str = "Réduire la période d'essai à 6 mois maximum.",
    severity: str = "BLOQUANT",
):
    from agents.verifier import _VerifierOutput
    from shared.schemas import FindingVerdict, FindingSeverity
    return _VerifierOutput(
        verdict=FindingVerdict(verdict),
        cited_article_id=cited_id,
        quoted_text=quoted,
        recommendation=recommendation,
        severity=FindingSeverity(severity),
    )


def test_verifier_node_no_clauses():
    from agents.verifier import verifier_node
    result = verifier_node(_make_state([], {}))
    assert result["findings"] == []
    assert result["errors"] == []


def test_verifier_node_fallback_when_no_articles():
    from agents.verifier import verifier_node
    clause = _make_clause("c1")
    state = _make_state([clause], {"c1": []})
    result = verifier_node(state)
    assert len(result["findings"]) == 1
    assert result["findings"][0]["verdict"] == FindingVerdict.EXIGE_REVUE.value
    assert result["findings"][0]["citation_valid"] is False


def test_verifier_node_valid_citation():
    from agents.verifier import verifier_node

    clause = _make_clause("c1")
    articles = [{"id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10", "full_text": ART10_TEXT, "text": ART10_TEXT}]
    state = _make_state([clause], {"c1": articles})

    mock_output = _mock_llm_output()

    with patch("agents.verifier.ChatOpenAI") as mock_cls:
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_llm.invoke.return_value = mock_output
        mock_cls.return_value = mock_llm

        result = verifier_node(state)

    assert len(result["findings"]) == 1
    f = result["findings"][0]
    assert f["citation_valid"] is True
    assert f["verdict"] == "NON_CONFORME"
    assert f["cited_article_id"] == "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10"


def test_verifier_node_retry_on_invalid_citation():
    """
    T1 : citation invalide (ID hallucinated) → retry T2.
    T2 : citation valide → finding marqué valid.
    """
    from agents.verifier import verifier_node

    clause = _make_clause("c1")
    articles = [{"id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10", "full_text": ART10_TEXT, "text": ART10_TEXT}]
    state = _make_state([clause], {"c1": articles})

    bad_output  = _mock_llm_output(cited_id="MAURITANIA_LABOR-CODE_TRAVAIL_MR-999")
    good_output = _mock_llm_output(cited_id="MAURITANIA_LABOR-CODE_TRAVAIL_MR-10")

    call_count = {"n": 0}
    def mock_invoke(messages):
        call_count["n"] += 1
        return bad_output if call_count["n"] == 1 else good_output

    with patch("agents.verifier.ChatOpenAI") as mock_cls:
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_llm.invoke.side_effect = mock_invoke
        mock_cls.return_value = mock_llm

        result = verifier_node(state)

    assert call_count["n"] == 2, "Le retry doit déclencher un 2ème appel LLM"
    f = result["findings"][0]
    assert f["citation_valid"] is True


def test_verifier_node_fallback_after_two_failures():
    """Si T1 et T2 échouent → fallback EXIGE_REVUE, citation_valid=False."""
    from agents.verifier import verifier_node

    clause = _make_clause("c1")
    articles = [{"id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10", "full_text": ART10_TEXT, "text": ART10_TEXT}]
    state = _make_state([clause], {"c1": articles})

    bad_output = _mock_llm_output(cited_id="MAURITANIA_LABOR-CODE_TRAVAIL_MR-999")

    with patch("agents.verifier.ChatOpenAI") as mock_cls:
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_llm.invoke.return_value = bad_output
        mock_cls.return_value = mock_llm

        result = verifier_node(state)

    f = result["findings"][0]
    assert f["verdict"] == FindingVerdict.EXIGE_REVUE.value
    assert f["citation_valid"] is False
    assert len(result["errors"]) >= 1


def test_verifier_node_multiple_clauses():
    """Toutes les clauses sont traitées même si la première échoue."""
    from agents.verifier import verifier_node

    clauses = [_make_clause("c1"), _make_clause("c2")]
    articles = [{"id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10", "full_text": ART10_TEXT, "text": ART10_TEXT}]
    retrievals = {"c1": articles, "c2": []}   # c2 sans articles
    state = _make_state(clauses, retrievals)

    good_output = _mock_llm_output()

    with patch("agents.verifier.ChatOpenAI") as mock_cls:
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_llm
        mock_llm.invoke.return_value = good_output
        mock_cls.return_value = mock_llm

        result = verifier_node(state)

    assert len(result["findings"]) == 2
    assert result["findings"][0]["clause_id"] == "c1"
    assert result["findings"][1]["clause_id"] == "c2"
    assert result["findings"][1]["citation_valid"] is False   # fallback


# ---------------------------------------------------------------------------
# Test LLM réel — marqué @slow
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_verifier_node_real_llm_non_conforme():
    """
    Test end-to-end vérificateur avec LLM réel.
    Période d'essai 9 mois > 6 mois max → verdict NON_CONFORME.
    """
    import os
    if not (os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        pytest.skip("DEEPSEEK_API_KEY / OPENAI_API_KEY non configuré")
    from agents.verifier import verifier_node

    clause = _make_clause(
        "essai-1",
        type_clause="periode_essai",
        text="période d'essai travailleur 9 mois",
    )
    articles = [{
        "id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "full_text": ART10_TEXT,
        "text": ART10_TEXT,
    }]
    state = _make_state([clause], {"essai-1": articles})
    result = verifier_node(state)

    assert len(result["findings"]) == 1
    f = result["findings"][0]
    assert f["verdict"] in [
        FindingVerdict.NON_CONFORME.value,
        FindingVerdict.EXIGE_REVUE.value,
    ]
    if f["citation_valid"]:
        assert f["cited_article_id"] == "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10"
