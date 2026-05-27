"""
Test Jalon 1 — Validation des schémas Pydantic.
Critère PDF : schémas consommables par les 3 modules sans erreur.
Lance avec : pytest tests/test_schemas.py -v
"""
import pytest
from pydantic import ValidationError

from shared.schemas import (
    AgentState,
    Article,
    Associe,
    Clause,
    ClauseType,
    ContratsExtraction,
    Finding,
    FindingSeverity,
    FindingVerdict,
    Jurisdiction,
    StatutsExtraction,
)


# ---------------------------------------------------------------------------
# Clause
# ---------------------------------------------------------------------------

def test_clause_creation():
    c = Clause(type_clause=ClauseType.CAPITAL_SOCIAL, text="Le capital est de 1 000 000 FCFA.")
    assert c.clause_id is not None
    assert c.type_clause == ClauseType.CAPITAL_SOCIAL


def test_clause_with_jurisdiction():
    c = Clause(
        type_clause=ClauseType.PERIODE_ESSAI,
        text="La période d'essai est de 3 mois.",
        jurisdiction_hint=Jurisdiction.MAURITANIA_LABOR,
    )
    assert c.jurisdiction_hint == Jurisdiction.MAURITANIA_LABOR


# ---------------------------------------------------------------------------
# StatutsExtraction
# ---------------------------------------------------------------------------

def test_statuts_valid():
    s = StatutsExtraction(
        forme_sociale="SARL",
        denomination="Tech Sahel SARL",
        siege_social="Nouakchott, Mauritanie",
        objet_social="Services informatiques",
        duree_annees=99,
        capital_social_fcfa=1_000_000,
        parts_sociales_nb=1000,
        parts_sociales_valeur_fcfa=1000,
        associes=[Associe(nom="Ahmed Ould Baye", apport_fcfa=1_000_000, parts_nb=1000)],
        clauses=[
            Clause(type_clause=ClauseType.CAPITAL_SOCIAL, text="Capital de 1 000 000 FCFA."),
            Clause(type_clause=ClauseType.DUREE_SOCIETE, text="Durée 99 ans."),
        ],
    )
    assert s.forme_sociale == "SARL"
    assert s.duree_annees == 99
    assert len(s.clauses) == 2


def test_statuts_duree_over_99_rejected():
    with pytest.raises(ValidationError) as exc_info:
        StatutsExtraction(
            forme_sociale="SA",
            denomination="BadCo SA",
            siege_social="Nouakchott",
            objet_social="Commerce",
            duree_annees=100,   # violates Art. 28 AUSCGIE
            capital_social_fcfa=10_000_000,
            parts_sociales_nb=1000,
            parts_sociales_valeur_fcfa=10_000,
            associes=[],
            clauses=[],
        )
    assert "99" in str(exc_info.value)


def test_statuts_all_formes_sociales():
    for forme in ("SARL", "SA", "SAS", "SNC", "GIE"):
        s = StatutsExtraction(
            forme_sociale=forme,
            denomination=f"Test {forme}",
            siege_social="Dakar",
            objet_social="Test",
            duree_annees=50,
            capital_social_fcfa=5_000_000,
            parts_sociales_nb=500,
            parts_sociales_valeur_fcfa=10_000,
            associes=[],
            clauses=[],
        )
        assert s.forme_sociale == forme


# ---------------------------------------------------------------------------
# ContratsExtraction
# ---------------------------------------------------------------------------

def test_contrat_travail_cdi():
    c = ContratsExtraction(
        type_contrat="CDI",
        employeur="Société Minière MR",
        employe="Fatima Mint Ahmed",
        poste="Ingénieure",
        salaire_mensuel_fcfa=150_000,
        periode_essai_mois=3,
        est_cadre=False,
        age_employe=25,
        clauses=[
            Clause(type_clause=ClauseType.TYPE_CONTRAT, text="Contrat à durée indéterminée."),
            Clause(type_clause=ClauseType.PERIODE_ESSAI, text="Période d'essai de 3 mois."),
        ],
    )
    assert c.type_contrat == "CDI"
    assert c.periode_essai_mois == 3


def test_contrat_travail_cdd_avec_visa():
    c = ContratsExtraction(
        type_contrat="CDD",
        employeur="ONG Sahel",
        employe="Mohamed Vall",
        poste="Technicien",
        duree_mois=6,
        salaire_mensuel_fcfa=80_000,
        periode_essai_mois=1,
        visa_inspection=True,   # Art. 18: CDD > 3 mois → visa obligatoire
        age_employe=20,
        clauses=[],
    )
    assert c.visa_inspection is True
    assert c.duree_mois == 6


# ---------------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------------

def test_article_ohada():
    a = Article(
        id="OHADA-AUSCGIE-311",
        jurisdiction="ohada",
        code_name="AUSCGIE",
        article_number="311",
        hierarchy_path="Livre 2 > Titre 2 > Chapitre 1",
        full_text="Le montant du capital social de la SARL est fixé librement par les associés. "
                  "Il ne peut être inférieur à un million (1 000 000) de francs CFA.",
        language="fr",
    )
    assert a.id == "OHADA-AUSCGIE-311"
    assert a.score is None


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------

def test_finding_non_conforme():
    f = Finding(
        clause_id="abc123",
        verdict=FindingVerdict.NON_CONFORME,
        cited_article_id="OHADA-AUSCGIE-311",
        quoted_text="inférieur à un million (1 000 000) de francs CFA",
        recommendation="Augmenter le capital social à 1 000 000 FCFA minimum.",
        severity=FindingSeverity.BLOQUANT,
        citation_valid=True,
    )
    assert f.verdict == FindingVerdict.NON_CONFORME
    assert f.severity == FindingSeverity.BLOQUANT


def test_finding_default_citation_invalid():
    f = Finding(
        clause_id="xyz",
        verdict=FindingVerdict.CONFORME,
        cited_article_id="OHADA-AUSCGIE-28",
        quoted_text="ne peut excéder quatre-vingt-dix-neuf ans",
    )
    assert f.citation_valid is False  # default avant passage par citation_guard


# ---------------------------------------------------------------------------
# AgentState structure
# ---------------------------------------------------------------------------

def test_agent_state_keys():
    required_keys = {
        "contract_id", "contract_text", "jurisdiction",
        "extracted", "clauses", "retrievals", "findings", "errors",
    }
    hints = AgentState.__annotations__
    assert required_keys.issubset(set(hints.keys()))
