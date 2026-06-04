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
    Clause,
    ClauseType,
    ContratsExtraction,
    Finding,
    FindingSeverity,
    FindingVerdict,
    Jurisdiction,
)


# ---------------------------------------------------------------------------
# Clause
# ---------------------------------------------------------------------------

def test_clause_creation():
    c = Clause(type_clause=ClauseType.TYPE_CONTRAT, text="Contrat à durée déterminée.")
    assert c.clause_id is not None
    assert c.type_clause == ClauseType.TYPE_CONTRAT


def test_clause_with_jurisdiction():
    c = Clause(
        type_clause=ClauseType.PERIODE_ESSAI,
        text="La période d'essai est de 3 mois.",
        jurisdiction_hint=Jurisdiction.MAURITANIA_LABOR,
    )
    assert c.jurisdiction_hint == Jurisdiction.MAURITANIA_LABOR


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


def test_contrat_all_types():
    for t in ("CDI", "CDD", "CTT", "Stage", "Autre"):
        c = ContratsExtraction(
            type_contrat=t,
            employeur="Employeur Test",
            employe="Employé Test",
            poste="Poste Test",
        )
        assert c.type_contrat == t


# ---------------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------------

def test_article_mauritania_labor():
    a = Article(
        id="MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        jurisdiction="mauritania_labor",
        code_name="CODE_TRAVAIL_MR",
        article_number="10",
        hierarchy_path="Titre 1 > Chapitre 1",
        full_text="Article 10 : La période d'essai ne peut excéder six mois pour les travailleurs.",
        language="fr",
    )
    assert a.id == "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10"
    assert a.score is None


def test_article_coc():
    a = Article(
        id="MAURITANIA_LABOR-COC_MR-1",
        jurisdiction="mauritania_labor",
        code_name="COC_MR",
        article_number="1",
        full_text="Article 1 : Les obligations naissent d'un contrat...",
    )
    assert a.jurisdiction == "mauritania_labor"


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------

def test_finding_non_conforme():
    f = Finding(
        clause_id="abc123",
        verdict=FindingVerdict.NON_CONFORME,
        cited_article_id="MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        quoted_text="La période d'essai ne peut excéder six mois",
        recommendation="Réduire la période d'essai à 6 mois maximum.",
        severity=FindingSeverity.BLOQUANT,
        citation_valid=True,
    )
    assert f.verdict == FindingVerdict.NON_CONFORME
    assert f.severity == FindingSeverity.BLOQUANT


def test_finding_default_citation_invalid():
    f = Finding(
        clause_id="xyz",
        verdict=FindingVerdict.CONFORME,
        cited_article_id="MAURITANIA_LABOR-CODE_TRAVAIL_MR-153",
        quoted_text="L'âge minimum légal est de quatorze ans",
    )
    assert f.citation_valid is False   # default avant passage par citation_guard


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
