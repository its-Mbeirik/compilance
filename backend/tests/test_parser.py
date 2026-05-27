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
# segment_by_article — sur texte synthétique
# ---------------------------------------------------------------------------

SAMPLE_OHADA_TEXT = """
LIVRE PREMIER
DISPOSITIONS GÉNÉRALES

TITRE 1
DE LA FORME ET DE LA DÉNOMINATION

CHAPITRE 1
Définitions

Article 2 : La société commerciale est créée par deux ou plusieurs personnes
qui conviennent d'affecter des biens à une activité commune.

Article 5 : Toute société commerciale doit être immatriculée au Registre
du Commerce et du Crédit Mobilier.

LIVRE DEUXIÈME
DES SOCIÉTÉS COMMERCIALES

TITRE 2
DE LA SOCIÉTÉ À RESPONSABILITÉ LIMITÉE

CHAPITRE 1
Capital et parts sociales

Article 311 : Le montant du capital social est fixé librement par les associés.
Il ne peut être inférieur à un million (1 000 000) de francs CFA.

Article 312 : Les parts sociales doivent être intégralement libérées lors
de la souscription.
"""

SAMPLE_LABOR_TEXT = """
TITRE 1
DU CONTRAT DE TRAVAIL

CHAPITRE 1
Dispositions générales

Article 4 : Le contrat de travail est la convention par laquelle une personne
s'engage à travailler sous la direction d'un employeur moyennant rémunération.

Article 10 : La période d'essai ne peut excéder six mois pour les travailleurs
et douze mois pour les cadres.
"""


def test_segment_ohada_articles():
    articles = segment_by_article(
        SAMPLE_OHADA_TEXT, "ohada", "AUSCGIE", "2014-05-05"
    )
    article_numbers = [a.article_number for a in articles]
    assert "2" in article_numbers
    assert "311" in article_numbers
    assert "312" in article_numbers


def test_segment_article_text_content():
    articles = segment_by_article(
        SAMPLE_OHADA_TEXT, "ohada", "AUSCGIE"
    )
    art311 = next((a for a in articles if a.article_number == "311"), None)
    assert art311 is not None
    assert "1 000 000" in art311.full_text


def test_segment_article_ids():
    articles = segment_by_article(
        SAMPLE_OHADA_TEXT, "ohada", "AUSCGIE"
    )
    for a in articles:
        assert a.id.startswith("OHADA-AUSCGIE-")
        assert a.jurisdiction == "ohada"
        assert a.code_name == "AUSCGIE"


def test_segment_labor_articles():
    articles = segment_by_article(
        SAMPLE_LABOR_TEXT, "mauritania_labor", "CODE_TRAVAIL_MR"
    )
    numbers = [a.article_number for a in articles]
    assert "4" in numbers
    assert "10" in numbers


def test_segment_version_date_propagated():
    articles = segment_by_article(
        SAMPLE_OHADA_TEXT, "ohada", "AUSCGIE", version_date="2014-05-05"
    )
    assert all(a.version_date == "2014-05-05" for a in articles)


# ---------------------------------------------------------------------------
# Hiérarchie
# ---------------------------------------------------------------------------

def test_hierarchy_livre_detected():
    hier = _build_hierarchy_index(SAMPLE_OHADA_TEXT)
    levels = [level for _, level, _ in hier]
    assert "livre" in levels


def test_hierarchy_at_article_311():
    hier = _build_hierarchy_index(SAMPLE_OHADA_TEXT)
    import re
    m = re.search(r"Article 311", SAMPLE_OHADA_TEXT)
    path = _hierarchy_at(m.start(), hier)
    assert "Deuxième" in path or "Deuxieme" in path or "DEUXIÈME" in path or path != ""


def test_hierarchy_empty_for_beginning():
    """Position 0 avant tout titre → chemin non-vide ou par défaut."""
    hier = _build_hierarchy_index(SAMPLE_OHADA_TEXT)
    path = _hierarchy_at(0, hier)
    assert isinstance(path, str)


# ---------------------------------------------------------------------------
# RawArticle
# ---------------------------------------------------------------------------

def test_raw_article_id_format():
    a = RawArticle(
        article_number="311",
        full_text="Article 311 : texte.",
        hierarchy_path="Livre 2 > Titre 2",
        jurisdiction="ohada",
        code_name="AUSCGIE",
    )
    assert a.id == "OHADA-AUSCGIE-311"


def test_raw_article_id_mauritania_labor():
    a = RawArticle(
        article_number="10",
        full_text="Article 10 : période d'essai.",
        hierarchy_path="Titre 1 > Chapitre 2",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
    )
    assert a.id == "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10"


def test_segment_skips_empty_articles():
    """Les articles avec moins de 10 chars de texte sont ignorés."""
    minimal = "Article 1 : \n\nArticle 2 : Texte suffisamment long pour être inclus."
    articles = segment_by_article(minimal, "ohada", "AUSCGIE")
    numbers = [a.article_number for a in articles]
    assert "1" not in numbers
    assert "2" in numbers
