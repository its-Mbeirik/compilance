"""
Jalon 3 — Nœud Extracteur.
Appelle le LLM (structured output) pour extraire les données contractuelles
et génère les clauses de conformité à vérifier.
Supporte le français et l'arabe.
"""
import logging
import os
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from shared.schemas import (
    AgentState,
    Clause,
    ClauseType,
    ContratsExtraction,
    Jurisdiction,
)

logger = logging.getLogger(__name__)

# ── French prompts ─────────────────────────────────────────────────────────────

_SYSTEM_LABOR_FR = """\
Tu es un expert en droit du travail mauritanien \
(Code du Travail, Loi n° 2004-017 modifiée par Loi 2009-027).

Analyse le contrat de travail fourni et extrais avec précision toutes les informations structurées.
Pour la liste 'clauses', génère une entrée par point de conformité important, \
avec le texte EXACT tel qu'il apparaît dans le document."""

_FEW_SHOT_FR = """\
Exemple — CDD :
"M. Ba est engagé comme Développeur pour 6 mois. Période d'essai : 2 mois. \
Salaire : 180 000 FCFA/mois."
→ type_contrat="CDD", duree_mois=6, periode_essai_mois=2, salaire_mensuel_fcfa=180000
"""

# ── Arabic prompts ─────────────────────────────────────────────────────────────

_SYSTEM_LABOR_AR = """\
أنت خبير في قانون العمل الموريتاني \
(قانون العمل، القانون رقم 2004-017 المعدَّل بالقانون 2009-027).

حلِّل عقد العمل المقدَّم واستخرج جميع المعلومات المنظَّمة بدقة.
لقائمة 'clauses'، أنشئ مدخلاً لكل نقطة امتثال مهمة، \
مع النص الحرفي كما يظهر في الوثيقة."""

_FEW_SHOT_AR = """\
مثال — عقد محدد المدة:
"يُعيَّن السيد با بوصف مطوّر ويب لمدة 6 أشهر. فترة التجربة: شهران. الراتب: 180,000 فرنك أفريقي شهرياً."
→ type_contrat="CDD"، duree_mois=6، periode_essai_mois=2، salaire_mensuel_fcfa=180000
"""


def _generate_clauses(extracted: dict, jurisdiction: str) -> list[dict]:
    """
    Génère les clauses de conformité depuis les données extraites.
    Conserve les clauses déjà remplies par le LLM et ajoute les clauses
    déduites des champs structurés.
    """
    clauses: list[dict] = []
    seen_types: set[str] = set()

    for raw in extracted.get("clauses", []):
        if isinstance(raw, dict) and raw.get("type_clause"):
            clauses.append(raw)
            seen_types.add(raw["type_clause"])

    def _add(type_clause: ClauseType, text: str) -> None:
        if type_clause.value not in seen_types:
            c = Clause(
                type_clause=type_clause,
                text=text,
                jurisdiction_hint=Jurisdiction.MAURITANIA_LABOR,
            )
            clauses.append(c.model_dump())
            seen_types.add(type_clause.value)

    type_c    = extracted.get("type_contrat", "")
    periode   = extracted.get("periode_essai_mois")
    duree_mois = extracted.get("duree_mois")
    age       = extracted.get("age_employe")
    est_cadre = extracted.get("est_cadre", False)

    if periode is not None:
        label = "cadre" if est_cadre else "travailleur"
        _add(ClauseType.PERIODE_ESSAI, f"période d'essai {label} {periode} mois")
    if type_c == "CDD":
        _add(ClauseType.DUREE_CDD, f"CDD durée {duree_mois or '?'} mois visa inspection travail")
    if age is not None:
        _add(ClauseType.AGE_MINIMUM, f"âge minimum travail employe {age} ans")

    return clauses


def extractor_node(state: AgentState) -> dict[str, Any]:
    """Nœud Extracteur : texte contrat → extraction structurée + clauses de conformité."""
    contract_text = state["contract_text"]
    language      = state.get("language", "fr")

    system_msg = _SYSTEM_LABOR_AR if language == "ar" else _SYSTEM_LABOR_FR
    few_shot   = _FEW_SHOT_AR     if language == "ar" else _FEW_SHOT_FR

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
        temperature=0,
        max_tokens=4096,
    ).with_structured_output(ContratsExtraction, method="function_calling", include_raw=False)

    prompt = (
        f"{few_shot}\n\n---\n\n"
        f"{'الوثيقة المراد تحليلها' if language == 'ar' else 'Document à analyser'} :\n\n"
        f"{contract_text[:8000]}"
    )

    try:
        extraction = llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt),
        ])
        extracted_dict = extraction.model_dump()
        clauses = _generate_clauses(extracted_dict, "mauritania_labor")
        logger.info(
            "Extraction réussie: %d clauses (%s, lang=%s)",
            len(clauses),
            extracted_dict.get("type_contrat", "?"),
            language,
        )
        return {"extracted": extracted_dict, "clauses": clauses}
    except Exception as exc:
        logger.error("Erreur Extracteur: %s", exc)
        return {
            "extracted": {},
            "clauses": [],
            "errors": [f"Extracteur: {exc}"],
        }
