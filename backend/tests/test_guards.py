"""
Test Jalon 1 — Garde-fou de citation (citation_guard).
Critère PDF : taux de citations valides = 1.00
Lance avec : pytest tests/test_guards.py -v
"""
from shared.guards import citation_guard

ARTICLE_311_TEXT = (
    "Le montant du capital social de la SARL est fixé librement par les associés. "
    "Il ne peut être inférieur à un million (1 000 000) de francs CFA."
)

RETRIEVALS = {
    "clause_01": [
        {"id": "OHADA-AUSCGIE-311", "text": ARTICLE_311_TEXT},
        {"id": "OHADA-AUSCGIE-312", "text": "Les parts sociales sont égales..."},
    ]
}


def test_citation_valid():
    finding = {
        "clause_id": "clause_01",
        "cited_article_id": "OHADA-AUSCGIE-311",
        "quoted_text": "inférieur à un million (1 000 000) de francs CFA",
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is True
    assert msg == "OK"


def test_citation_hallucinated_id():
    finding = {
        "clause_id": "clause_01",
        "cited_article_id": "OHADA-AUSCGIE-999",   # n'existe pas dans top-5
        "quoted_text": "quelque chose",
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is False
    assert "inventé" in msg


def test_citation_wrong_quoted_text():
    finding = {
        "clause_id": "clause_01",
        "cited_article_id": "OHADA-AUSCGIE-311",
        "quoted_text": "ce texte n'est pas dans l'article",  # hallucination textuelle
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is False
    assert "non trouvée" in msg


def test_citation_unknown_clause_id():
    finding = {
        "clause_id": "clause_inconnu",
        "cited_article_id": "OHADA-AUSCGIE-311",
        "quoted_text": "texte",
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is False
    assert "absent" in msg


def test_citation_exact_full_text():
    finding = {
        "clause_id": "clause_01",
        "cited_article_id": "OHADA-AUSCGIE-311",
        "quoted_text": ARTICLE_311_TEXT,  # citation complète du texte
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is True
