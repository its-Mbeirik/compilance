"""
Jalon 3 — Nœud Extracteur.
Appelle Claude (structured output) pour extraire les données contractuelles
et génère les clauses de conformité à vérifier.
"""
import logging
from typing import Any

import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from shared.schemas import (
    AgentState,
    Clause,
    ClauseType,
    ContratsExtraction,
    Jurisdiction,
    StatutsExtraction,
)

logger = logging.getLogger(__name__)

_SYSTEM_OHADA = """Tu es un expert juridique OHADA spécialisé en droit des sociétés commerciales \
(Acte Uniforme du 30 janvier 2014 relatif au droit des sociétés commerciales et du GIE).

Analyse le document fourni et extrais avec précision toutes les informations structurées demandées.
Pour la liste 'clauses', génère une entrée par point de conformité important, \
avec le texte EXACT tel qu'il apparaît dans le document."""

_SYSTEM_LABOR = """Tu es un expert en droit du travail mauritanien \
(Code du Travail, Loi n° 2004-017 modifiée par Loi 2009-027).

Analyse le contrat de travail fourni et extrais avec précision toutes les informations structurées.
Pour la liste 'clauses', génère une entrée par point de conformité important, \
avec le texte EXACT tel qu'il apparaît dans le document."""

_FEW_SHOT_OHADA = """\
Exemple — Statuts SARL :
"La société est constituée sous forme de SARL dénommée TECH AFRICA. \
Capital : 2 000 000 FCFA. Durée : 99 ans. Siège : Nouakchott, Rue Mamadou Konaté."
→ forme_sociale="SARL", capital_social_fcfa=2000000, duree_annees=99,
   siege_social="Nouakchott, Rue Mamadou Konaté"
"""

_FEW_SHOT_LABOR = """\
Exemple — CDD :
"M. Ba est engagé comme Développeur pour 6 mois. Période d'essai : 2 mois. \
Salaire : 180 000 FCFA/mois."
→ type_contrat="CDD", duree_mois=6, periode_essai_mois=2, salaire_mensuel_fcfa=180000
"""


def _generate_clauses(extracted: dict, jurisdiction: str) -> list[dict]:
    """
    Génère les clauses de conformité depuis les données extraites.
    Si le LLM a déjà rempli la liste 'clauses', on les conserve.
    On ajoute les clauses clés déduites des champs structurés.
    """
    clauses: list[dict] = []
    seen_types: set[str] = set()

    # Récupère les clauses éventuellement extraites par le LLM
    for raw in extracted.get("clauses", []):
        if isinstance(raw, dict) and raw.get("type_clause"):
            clauses.append(raw)
            seen_types.add(raw["type_clause"])

    def _add(type_clause: ClauseType, text: str, hint: Jurisdiction) -> None:
        if type_clause.value not in seen_types:
            c = Clause(type_clause=type_clause, text=text, jurisdiction_hint=hint)
            clauses.append(c.model_dump())
            seen_types.add(type_clause.value)

    if jurisdiction == "ohada":
        forme = extracted.get("forme_sociale", "société")
        capital = extracted.get("capital_social_fcfa")
        duree = extracted.get("duree_annees")
        siege = extracted.get("siege_social", "")

        if capital is not None:
            _add(
                ClauseType.CAPITAL_SOCIAL,
                f"capital social {forme} {capital:,.0f} FCFA",
                Jurisdiction.OHADA,
            )
        if duree is not None:
            _add(
                ClauseType.DUREE_SOCIETE,
                f"durée société {forme} {duree} ans",
                Jurisdiction.OHADA,
            )
        if siege:
            _add(
                ClauseType.SIEGE_SOCIAL,
                f"siège social société: {siege}",
                Jurisdiction.OHADA,
            )
        _add(
            ClauseType.MENTIONS_OBLIGATOIRES,
            f"mentions obligatoires statuts {forme}: dénomination, objet, capital, siège, durée",
            Jurisdiction.OHADA,
        )
        if forme == "SA":
            _add(
                ClauseType.LIBERATION_CAPITAL,
                f"libération capital SA quart souscription {capital or 0:,.0f} FCFA",
                Jurisdiction.OHADA,
            )

    else:  # mauritania_labor
        type_c = extracted.get("type_contrat", "")
        periode = extracted.get("periode_essai_mois")
        duree_mois = extracted.get("duree_mois")
        age = extracted.get("age_employe")
        est_cadre = extracted.get("est_cadre", False)

        if periode is not None:
            label = "cadre" if est_cadre else "travailleur"
            _add(
                ClauseType.PERIODE_ESSAI,
                f"période d'essai {label} {periode} mois",
                Jurisdiction.MAURITANIA_LABOR,
            )
        if type_c == "CDD":
            _add(
                ClauseType.DUREE_CDD,
                f"CDD durée {duree_mois or '?'} mois visa inspection travail",
                Jurisdiction.MAURITANIA_LABOR,
            )
        if age is not None:
            _add(
                ClauseType.AGE_MINIMUM,
                f"âge minimum travail employe {age} ans",
                Jurisdiction.MAURITANIA_LABOR,
            )

    return clauses


def extractor_node(state: AgentState) -> dict[str, Any]:
    """Nœud Extracteur : texte contrat → extraction structurée + clauses de conformité."""
    jurisdiction = state["jurisdiction"]
    contract_text = state["contract_text"]

    schema = StatutsExtraction if jurisdiction == "ohada" else ContratsExtraction
    system_msg = _SYSTEM_OHADA if jurisdiction == "ohada" else _SYSTEM_LABOR
    few_shot = _FEW_SHOT_OHADA if jurisdiction == "ohada" else _FEW_SHOT_LABOR

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
        temperature=0,
        max_tokens=4096,
    ).with_structured_output(schema, method="function_calling", include_raw=False)

    prompt = (
        f"{few_shot}\n\n---\n\n"
        f"Document à analyser :\n\n{contract_text[:8000]}"
    )

    try:
        extraction = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt),
        ])
        extracted_dict = extraction.model_dump()
        clauses = _generate_clauses(extracted_dict, jurisdiction)
        logger.info(
            f"Extraction réussie: {len(clauses)} clauses "
            f"({jurisdiction}, {extracted_dict.get('forme_sociale') or extracted_dict.get('type_contrat', '?')})"
        )
        return {"extracted": extracted_dict, "clauses": clauses}
    except Exception as exc:
        logger.error(f"Erreur Extracteur: {exc}")
        return {
            "extracted": {},
            "clauses": [],
            "errors": [f"Extracteur: {exc}"],
        }
