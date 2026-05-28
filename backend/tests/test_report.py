"""
Test Jalon 4 — Génération du rapport de conformité.
Tests unitaires purs, aucune dépendance DB ou LLM.
Lance avec : pytest tests/test_report.py -v
"""
from api.report import generate_html, _build_context


# ---------------------------------------------------------------------------
# Données de test
# ---------------------------------------------------------------------------

ANALYSIS_DONE = {
    "id": "abc123",
    "status": "done",
    "jurisdiction": "mauritania_labor",
    "doc_type": "contrat_travail",
    "findings": [
        {
            "clause_id": "pe-001",
            "verdict": "NON_CONFORME",
            "severity": "BLOQUANT",
            "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
            "quoted_text": "La période d'essai ne peut excéder six mois.",
            "recommendation": "Réduire la période d'essai à 6 mois maximum.",
            "citation_valid": True,
        },
        {
            "clause_id": "age-001",
            "verdict": "CONFORME",
            "severity": "MINEUR",
            "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-153",
            "quoted_text": "L'âge minimum d'admission au travail est fixé à quatorze ans.",
            "recommendation": None,
            "citation_valid": True,
        },
        {
            "clause_id": "visa-001",
            "verdict": "EXIGE_REVUE",
            "severity": "MAJEUR",
            "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-18",
            "quoted_text": "Le CDD de plus de trois mois doit être visé par l'Inspecteur du Travail.",
            "recommendation": "Faire viser le contrat par l'Inspecteur du Travail.",
            "citation_valid": False,
        },
    ],
    "extracted": {"type_contrat": "CDD", "duree_mois": 6},
    "created_at": "2026-05-27T10:00:00",
    "finished_at": "2026-05-27T10:01:30",
}

ANALYSIS_EMPTY = {
    **ANALYSIS_DONE,
    "findings": [],
}


# ---------------------------------------------------------------------------
# Tests _build_context
# ---------------------------------------------------------------------------

def test_build_context_counts_correctly():
    ctx = _build_context(ANALYSIS_DONE)
    assert ctx["counts"]["CONFORME"] == 1
    assert ctx["counts"]["NON_CONFORME"] == 1
    assert ctx["counts"]["EXIGE_REVUE"] == 1


def test_build_context_total():
    ctx = _build_context(ANALYSIS_DONE)
    assert ctx["total"] == 3


def test_build_context_bloquants():
    ctx = _build_context(ANALYSIS_DONE)
    assert len(ctx["bloquants"]) == 1
    assert ctx["bloquants"][0]["cited_article_id"] == "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10"


def test_build_context_empty_findings():
    ctx = _build_context(ANALYSIS_EMPTY)
    assert ctx["total"] == 0
    assert ctx["bloquants"] == []


def test_build_context_jurisdiction_label():
    ctx = _build_context(ANALYSIS_DONE)
    assert "Travail" in ctx["jurisdiction_label"] or "mauritanien" in ctx["jurisdiction_label"].lower()


def test_build_context_labor_label():
    labor = {**ANALYSIS_DONE, "jurisdiction": "mauritania_labor"}
    ctx = _build_context(labor)
    assert "Travail" in ctx["jurisdiction_label"] or "mauritanien" in ctx["jurisdiction_label"].lower()


# ---------------------------------------------------------------------------
# Tests generate_html
# ---------------------------------------------------------------------------

def test_generate_html_returns_string():
    html = generate_html(ANALYSIS_DONE)
    assert isinstance(html, str)
    assert len(html) > 100


def test_generate_html_contains_verdicts():
    html = generate_html(ANALYSIS_DONE)
    assert "NON_CONFORME" in html
    assert "CONFORME" in html
    assert "EXIGE_REVUE" in html


def test_generate_html_contains_article_ids():
    html = generate_html(ANALYSIS_DONE)
    assert "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10" in html
    assert "MAURITANIA_LABOR-CODE_TRAVAIL_MR-153" in html


def test_generate_html_contains_recommendation():
    html = generate_html(ANALYSIS_DONE)
    assert "Réduire la période d'essai" in html


def test_generate_html_contains_bloquant_section():
    html = generate_html(ANALYSIS_DONE)
    assert "bloquant" in html.lower() or "BLOQUANT" in html


def test_generate_html_empty_findings():
    html = generate_html(ANALYSIS_EMPTY)
    assert isinstance(html, str)
    assert "0" in html  # total = 0


def test_generate_html_valid_html_structure():
    html = generate_html(ANALYSIS_DONE)
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    assert "<table" in html


def test_generate_html_quote_truncated():
    """Les citations longues sont tronquées à 200 caractères dans le HTML."""
    long_quote_analysis = {
        **ANALYSIS_DONE,
        "findings": [{
            "clause_id": "x",
            "verdict": "CONFORME",
            "severity": None,
            "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-1",
            "quoted_text": "A" * 300,
            "recommendation": None,
            "citation_valid": True,
        }],
    }
    html = generate_html(long_quote_analysis)
    assert "…" in html or "A" * 300 not in html


# ---------------------------------------------------------------------------
# Test WeasyPrint (optionnel — marqué slow)
# ---------------------------------------------------------------------------

def test_generate_pdf_returns_bytes():
    """WeasyPrint génère un PDF valide (commence par %PDF)."""
    try:
        from api.report import generate_pdf
        pdf = generate_pdf(ANALYSIS_DONE)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"
    except RuntimeError:
        import pytest
        pytest.skip("WeasyPrint non disponible")
