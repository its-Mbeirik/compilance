"""
Test Jalon 1 — Garde-fou de citation (citation_guard).
Critère PDF : taux de citations valides = 1.00
Lance avec : pytest tests/test_guards.py -v
"""
from shared.guards import citation_guard

ARTICLE_10_TEXT = (
    "Article 10 : La période d'essai ne peut excéder six (6) mois pour les travailleurs "
    "et douze (12) mois pour les cadres et assimilés."
)

RETRIEVALS = {
    "clause_01": [
        {"id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",  "text": ARTICLE_10_TEXT},
        {"id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-153", "text": "Article 153 : L'âge minimum d'admission à l'emploi est fixé à quatorze ans."},
    ]
}


def test_citation_valid():
    finding = {
        "clause_id": "clause_01",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "ne peut excéder six (6) mois pour les travailleurs",
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is True
    assert msg == "OK"


def test_citation_hallucinated_id():
    finding = {
        "clause_id": "clause_01",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-999",   # n'existe pas dans top-5
        "quoted_text": "quelque chose",
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is False
    assert "inventé" in msg


def test_citation_wrong_quoted_text():
    finding = {
        "clause_id": "clause_01",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "ce texte n'est pas dans l'article",   # hallucination textuelle
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is False
    assert "non trouvée" in msg


def test_citation_unknown_clause_id():
    finding = {
        "clause_id": "clause_inconnu",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "texte",
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is False
    assert "absent" in msg


def test_citation_exact_full_text():
    finding = {
        "clause_id": "clause_01",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": ARTICLE_10_TEXT,   # citation complète du texte
    }
    ok, msg = citation_guard(finding, RETRIEVALS)
    assert ok is True
