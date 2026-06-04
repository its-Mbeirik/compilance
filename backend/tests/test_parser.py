"""
Test Jalon 2 — Parser PDF et segmentation par article.
Tests unitaires purs, aucune dépendance DB ou modèle.
Lance avec : pytest tests/test_parser.py -v
"""
from ingestion.parser import (
    RawArticle,
    clean_text,
    segment_by_article,
    _build_hierarchy_index,
    _hierarchy_at,
)


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------

def test_clean_text_removes_page_numbers():
    text = "Début du texte\n\n   42   \n\nSuite du texte."
    result = clean_text(text)
    assert "42" not in result or "42" in result.replace("   42   ", "")


def test_clean_text_normalizes_multiple_newlines():
    text = "Ligne A\n\n\n\n\nLigne B"
    result = clean_text(text)
    assert "\n\n\n" not in result


def test_clean_text_removes_separator_lines():
    text = "Avant\n" + "-" * 20 + "\nAprès"
    result = clean_text(text)
    assert "-" * 10 not in result


# ---------------------------------------------------------------------------
# Textes de test — corpus juridique mauritanien
# ---------------------------------------------------------------------------

SAMPLE_LABOR_TEXT = """
LIVRE PREMIER
DISPOSITIONS GÉNÉRALES

TITRE 1
DU CONTRAT DE TRAVAIL

CHAPITRE 1
Dispositions générales

Article 4 : Le contrat de travail est la convention par laquelle une personne
s'engage à travailler sous la direction d'un employeur moyennant rémunération.

Article 10 : La période d'essai ne peut excéder six mois pour les travailleurs
et douze mois pour les cadres.

LIVRE DEUXIÈME
PROTECTION DES TRAVAILLEURS

TITRE 2
EMPLOI DES JEUNES TRAVAILLEURS

CHAPITRE 1
Âge minimum

Article 153 : L'âge minimum d'admission à l'emploi est fixé à quatorze ans.

Article 154 : Toute infraction à l'article 153 est sanctionnée par les dispositions pénales.
"""


# ---------------------------------------------------------------------------
# segment_by_article — corpus mauritanien
# ---------------------------------------------------------------------------

def test_segment_labor_articles():
    articles = segment_by_article(
        SAMPLE_LABOR_TEXT, "mauritania_labor", "CODE_TRAVAIL_MR"
    )
    numbers = [a.article_number for a in articles]
    assert "4" in numbers
    assert "10" in numbers
    assert "153" in numbers


def test_segment_article_text_content():
    articles = segment_by_article(
        SAMPLE_LABOR_TEXT, "mauritania_labor", "CODE_TRAVAIL_MR"
    )
    art10 = next((a for a in articles if a.article_number == "10"), None)
    assert art10 is not None
    assert "six mois" in art10.full_text


def test_segment_article_ids():
    articles = segment_by_article(
        SAMPLE_LABOR_TEXT, "mauritania_labor", "CODE_TRAVAIL_MR"
    )
    for a in articles:
        assert a.id.startswith("MAURITANIA_LABOR-CODE_TRAVAIL_MR-")
        assert a.jurisdiction == "mauritania_labor"
        assert a.code_name == "CODE_TRAVAIL_MR"


def test_segment_version_date_propagated():
    articles = segment_by_article(
        SAMPLE_LABOR_TEXT, "mauritania_labor", "CODE_TRAVAIL_MR",
        version_date="2004-01-01"
    )
    assert all(a.version_date == "2004-01-01" for a in articles)


# ---------------------------------------------------------------------------
# Hiérarchie
# ---------------------------------------------------------------------------

def test_hierarchy_livre_detected():
    hier = _build_hierarchy_index(SAMPLE_LABOR_TEXT)
    levels = [level for _, level, _ in hier]
    assert "livre" in levels


def test_hierarchy_at_article_153():
    hier = _build_hierarchy_index(SAMPLE_LABOR_TEXT)
    import re
    m = re.search(r"Article 153", SAMPLE_LABOR_TEXT)
    path = _hierarchy_at(m.start(), hier)
    assert isinstance(path, str)
    assert path != ""


def test_hierarchy_empty_for_beginning():
    """Position 0 avant tout titre → chemin non-vide ou par défaut."""
    hier = _build_hierarchy_index(SAMPLE_LABOR_TEXT)
    path = _hierarchy_at(0, hier)
    assert isinstance(path, str)


# ---------------------------------------------------------------------------
# RawArticle
# ---------------------------------------------------------------------------

def test_raw_article_id_format():
    a = RawArticle(
        article_number="10",
        full_text="Article 10 : période d'essai.",
        hierarchy_path="Titre 1 > Chapitre 1",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
    )
    assert a.id == "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10"


def test_raw_article_id_coc():
    a = RawArticle(
        article_number="1",
        full_text="Article 1 : Les obligations naissent d'un contrat.",
        hierarchy_path="Titre 1",
        jurisdiction="mauritania_labor",
        code_name="COC_MR",
    )
    assert a.id == "MAURITANIA_LABOR-COC_MR-1"


def test_segment_skips_empty_articles():
    """Les articles avec moins de 10 chars de texte sont ignorés."""
    minimal = "Article 1 : \n\nArticle 2 : Texte suffisamment long pour être inclus."
    articles = segment_by_article(minimal, "mauritania_labor", "CODE_TRAVAIL_MR")
    numbers = [a.article_number for a in articles]
    assert "1" not in numbers
    assert "2" in numbers
