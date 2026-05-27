"""
Test Jalon 3 — Nœud Extracteur.
Tests unitaires (sans LLM) sur _generate_clauses + tests d'intégration LLM.
Lance avec :
    pytest tests/test_extractor.py -v                   # unit only
    pytest tests/test_extractor.py -v -m slow           # + LLM
"""
import pytest

from agents.extractor import _generate_clauses
from shared.schemas import ClauseType


# ---------------------------------------------------------------------------
# Données synthétiques
# ---------------------------------------------------------------------------

SARL_EXTRACTION = {
    "forme_sociale": "SARL",
    "denomination": "TECH AFRICA SARL",
    "siege_social": "Nouakchott, Avenue Gamal Abdel Nasser",
    "objet_social": "Développement logiciel",
    "duree_annees": 99,
    "capital_social_fcfa": 2_000_000,
    "parts_sociales_nb": 200,
    "parts_sociales_valeur_fcfa": 10_000,
    "associes": [],
    "governing_law_clause": None,
    "clauses": [],
}

SA_EXTRACTION = {
    **SARL_EXTRACTION,
    "forme_sociale": "SA",
    "capital_social_fcfa": 15_000_000,
}

CDD_EXTRACTION = {
    "type_contrat": "CDD",
    "employeur": "ACME SA",
    "employe": "Moussa Diallo",
    "poste": "Développeur",
    "date_debut": "2026-01-01",
    "date_fin": "2026-07-01",
    "duree_mois": 6,
    "salaire_mensuel_fcfa": 180_000,
    "periode_essai_mois": 2,
    "est_cadre": False,
    "age_employe": 25,
    "visa_inspection": True,
    "clauses": [],
}

CDI_EXTRACTION = {
    **CDD_EXTRACTION,
    "type_contrat": "CDI",
    "date_fin": None,
    "duree_mois": None,
}


# ---------------------------------------------------------------------------
# Tests _generate_clauses — OHADA
# ---------------------------------------------------------------------------

def test_sarl_generates_capital_clause():
    clauses = _generate_clauses(SARL_EXTRACTION, "ohada")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.CAPITAL_SOCIAL.value in types


def test_sarl_generates_duree_clause():
    clauses = _generate_clauses(SARL_EXTRACTION, "ohada")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.DUREE_SOCIETE.value in types


def test_sarl_generates_siege_clause():
    clauses = _generate_clauses(SARL_EXTRACTION, "ohada")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.SIEGE_SOCIAL.value in types


def test_sarl_generates_mentions_clause():
    clauses = _generate_clauses(SARL_EXTRACTION, "ohada")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.MENTIONS_OBLIGATOIRES.value in types


def test_sa_generates_liberation_clause():
    clauses = _generate_clauses(SA_EXTRACTION, "ohada")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.LIBERATION_CAPITAL.value in types


def test_sarl_no_liberation_clause():
    clauses = _generate_clauses(SARL_EXTRACTION, "ohada")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.LIBERATION_CAPITAL.value not in types


def test_capital_value_in_clause_text():
    clauses = _generate_clauses(SARL_EXTRACTION, "ohada")
    cap_clause = next(c for c in clauses if c["type_clause"] == ClauseType.CAPITAL_SOCIAL.value)
    assert "2" in cap_clause["text"] and "000" in cap_clause["text"]


def test_clauses_have_required_keys():
    clauses = _generate_clauses(SARL_EXTRACTION, "ohada")
    for c in clauses:
        assert "clause_id" in c
        assert "type_clause" in c
        assert "text" in c
        assert len(c["clause_id"]) > 0
        assert len(c["text"]) > 0


def test_clauses_ids_unique():
    clauses = _generate_clauses(SARL_EXTRACTION, "ohada")
    ids = [c["clause_id"] for c in clauses]
    assert len(ids) == len(set(ids))


def test_no_duplicate_clause_types_ohada():
    clauses = _generate_clauses(SARL_EXTRACTION, "ohada")
    types = [c["type_clause"] for c in clauses]
    assert len(types) == len(set(types)), f"Doublons: {types}"


# ---------------------------------------------------------------------------
# Tests _generate_clauses — Code du Travail
# ---------------------------------------------------------------------------

def test_cdd_generates_periode_essai():
    clauses = _generate_clauses(CDD_EXTRACTION, "mauritania_labor")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.PERIODE_ESSAI.value in types


def test_cdd_generates_duree_cdd():
    clauses = _generate_clauses(CDD_EXTRACTION, "mauritania_labor")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.DUREE_CDD.value in types


def test_cdd_generates_age_minimum():
    clauses = _generate_clauses(CDD_EXTRACTION, "mauritania_labor")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.AGE_MINIMUM.value in types


def test_cdi_no_duree_cdd_clause():
    clauses = _generate_clauses(CDI_EXTRACTION, "mauritania_labor")
    types = [c["type_clause"] for c in clauses]
    assert ClauseType.DUREE_CDD.value not in types


def test_no_duplicate_clause_types_labor():
    clauses = _generate_clauses(CDD_EXTRACTION, "mauritania_labor")
    types = [c["type_clause"] for c in clauses]
    assert len(types) == len(set(types)), f"Doublons: {types}"


def test_llm_clauses_preserved():
    """Les clauses pré-remplies par le LLM ne sont pas dupliquées."""
    with_llm_clauses = dict(SARL_EXTRACTION)
    with_llm_clauses["clauses"] = [{
        "clause_id": "abc12345",
        "type_clause": ClauseType.CAPITAL_SOCIAL.value,
        "text": "Le capital est de 2 000 000 FCFA conformément aux statuts.",
        "jurisdiction_hint": "ohada",
    }]
    clauses = _generate_clauses(with_llm_clauses, "ohada")
    cap_clauses = [c for c in clauses if c["type_clause"] == ClauseType.CAPITAL_SOCIAL.value]
    assert len(cap_clauses) == 1, "La clause capital ne doit apparaître qu'une fois"


# ---------------------------------------------------------------------------
# Test LLM réel — marqué @slow
# ---------------------------------------------------------------------------

SAMPLE_SARL_TEXT = """\
STATUTS DE LA SOCIÉTÉ TECH MAURITANIE SARL

Article 1 — Forme
Il est constitué une Société à Responsabilité Limitée régie par l'Acte Uniforme OHADA.

Article 2 — Dénomination
La société a pour dénomination : TECH MAURITANIE SARL.

Article 3 — Siège social
Le siège social est fixé à Nouakchott, Avenue Gamal Abdel Nasser, Immeuble Sahara.

Article 4 — Objet social
La société a pour objet : le développement de logiciels et la prestation de services informatiques.

Article 5 — Durée
La durée de la société est fixée à quatre-vingt-dix-neuf (99) ans.

Article 6 — Capital social
Le capital social est fixé à la somme de DEUX MILLIONS (2 000 000) de francs CFA,
divisé en 200 parts sociales de dix mille (10 000) FCFA chacune, intégralement libérées.

Article 7 — Associés
- M. Cheikh Ould Sidi : 100 parts, apport 1 000 000 FCFA
- Mme Aïcha Mint Brahim : 100 parts, apport 1 000 000 FCFA
"""


@pytest.mark.slow
def test_extractor_node_real_llm_ohada():
    """Test d'intégration : extraction réelle avec Claude sur un statut SARL."""
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY non configuré")
    from agents.extractor import extractor_node
    state = {
        "contract_id": "test-001",
        "contract_text": SAMPLE_SARL_TEXT,
        "jurisdiction": "ohada",
        "extracted": {},
        "clauses": [],
        "retrievals": {},
        "findings": [],
        "errors": [],
    }
    result = extractor_node(state)
    assert "extracted" in result
    assert "clauses" in result
    assert len(result["errors"] if "errors" in result else []) == 0
    extracted = result["extracted"]
    assert extracted.get("forme_sociale") == "SARL"
    assert extracted.get("capital_social_fcfa") == 2_000_000
    assert result["clauses"], "Au moins une clause doit être générée"


SAMPLE_CDD_TEXT = """\
CONTRAT À DURÉE DÉTERMINÉE

Entre :
- La société ACME SA, représentée par M. Ahmed Ould Mohamed, employeur
- M. Ibrahima Diallo, né le 15/03/2000, employé

Il est convenu ce qui suit :

Article 1 — Engagement
M. Ibrahima Diallo est engagé en qualité de Développeur Web pour une durée déterminée \
de six (6) mois, du 1er janvier 2026 au 1er juillet 2026.
Ce contrat a été visé par l'Inspecteur du Travail.

Article 2 — Période d'essai
La période d'essai est fixée à deux (2) mois.

Article 3 — Rémunération
Le salaire mensuel brut est de cent quatre-vingt mille (180 000) francs CFA.
"""


@pytest.mark.slow
def test_extractor_node_real_llm_labor():
    """Test d'intégration : extraction réelle avec Claude sur un CDD."""
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY non configuré")
    from agents.extractor import extractor_node
    state = {
        "contract_id": "test-002",
        "contract_text": SAMPLE_CDD_TEXT,
        "jurisdiction": "mauritania_labor",
        "extracted": {},
        "clauses": [],
        "retrievals": {},
        "findings": [],
        "errors": [],
    }
    result = extractor_node(state)
    assert "extracted" in result
    extracted = result["extracted"]
    assert extracted.get("type_contrat") == "CDD"
    assert extracted.get("duree_mois") == 6
    assert result["clauses"], "Au moins une clause doit être générée"
