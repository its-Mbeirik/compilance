"""
Jalon 3 — Nœud Vérificateur.
Pour chaque clause + top-5 articles → Claude génère un Finding → citation_guard.
Retry unique si la citation est invalide ; fallback EXIGE_REVUE sinon.
"""
import logging
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from shared.guards import citation_guard
from shared.schemas import (
    AgentState,
    FindingSeverity,
    FindingVerdict,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schéma de sortie LLM (Finding sans citation_valid — positionné par nous)
# ---------------------------------------------------------------------------

class _VerifierOutput(BaseModel):
    verdict: FindingVerdict = Field(
        description="CONFORME, NON_CONFORME, ou EXIGE_REVUE"
    )
    cited_article_id: str = Field(
        description="ID exact de l'article, ex: 'OHADA-AUSCGIE-311'"
    )
    quoted_text: str = Field(
        description=(
            "Sous-chaîne EXACTE et LITTÉRALE de l'article cité. "
            "Copier mot-à-mot sans modification."
        )
    )
    recommendation: Optional[str] = Field(
        default=None,
        description="Recommandation correctrice si NON_CONFORME ou EXIGE_REVUE"
    )
    severity: Optional[FindingSeverity] = Field(
        default=None,
        description=(
            "BLOQUANT (capital, âge minimum), "
            "MAJEUR (durée, visa inspection), "
            "MINEUR (mentions, autres)"
        )
    )


_SYSTEM_VERIFIER = """\
Tu es un expert en conformité juridique. Tu dois vérifier si une clause contractuelle \
respecte la réglementation en vigueur.

Règles absolues :
1. Tu DOIS citer un article parmi ceux fournis — aucun autre.
2. Le champ 'quoted_text' doit être copié MOT-À-MOT depuis l'article cité.
   Toute modification, même mineure, est interdite.
3. Sévérité : BLOQUANT = capital / âge / forme sociale ;
              MAJEUR   = durée / visa / libération ;
              MINEUR   = mentions / autres.
"""


def _format_articles(articles: list[dict]) -> str:
    lines = []
    for i, art in enumerate(articles, 1):
        lines.append(f"[{i}] ID: {art['id']}\n{art.get('full_text', art.get('text', ''))}\n")
    return "\n".join(lines)


def _call_llm(
    llm,
    clause: dict,
    articles: list[dict],
    extra_feedback: str = "",
) -> Optional[_VerifierOutput]:
    """Appelle le LLM et retourne le _VerifierOutput ou None en cas d'erreur."""
    article_block = _format_articles(articles)
    feedback_block = f"\n\nFeedback précédent :\n{extra_feedback}" if extra_feedback else ""

    prompt = (
        f"CLAUSE À VÉRIFIER :\n"
        f"  Type  : {clause.get('type_clause', '?')}\n"
        f"  Texte : {clause.get('text', '')}\n\n"
        f"ARTICLES JURIDIQUES (top-5) :\n{article_block}"
        f"{feedback_block}"
    )
    try:
        return llm.invoke([
            SystemMessage(content=_SYSTEM_VERIFIER),
            HumanMessage(content=prompt),
        ])
    except Exception as exc:
        logger.error(f"Erreur LLM vérificateur: {exc}")
        return None


def _build_finding(
    clause_id: str,
    output: _VerifierOutput,
    citation_valid: bool,
) -> dict:
    return {
        "clause_id": clause_id,
        "verdict": output.verdict.value,
        "cited_article_id": output.cited_article_id,
        "quoted_text": output.quoted_text,
        "recommendation": output.recommendation,
        "severity": output.severity.value if output.severity else None,
        "citation_valid": citation_valid,
    }


def _fallback_finding(clause_id: str, reason: str) -> dict:
    return {
        "clause_id": clause_id,
        "verdict": FindingVerdict.EXIGE_REVUE.value,
        "cited_article_id": "",
        "quoted_text": "",
        "recommendation": f"Vérification manuelle requise — {reason}",
        "severity": FindingSeverity.MINEUR.value,
        "citation_valid": False,
    }


def verifier_node(state: AgentState) -> dict[str, Any]:
    """
    Nœud Vérificateur :
    - Pour chaque clause dans state['clauses']
    - Récupère les top-5 articles depuis state['retrievals']
    - Génère un Finding via Claude
    - Valide la citation (citation_guard)
    - Retry unique si la citation est invalide
    - Accumule les findings (operator.add via Annotated)
    """
    clauses: list[dict] = state.get("clauses", [])
    retrievals: dict[str, list[dict]] = state.get("retrievals", {})
    findings: list[dict] = []
    errors: list[str] = []

    if not clauses:
        return {"findings": [], "errors": []}

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0,
        max_tokens=2048,
    ).with_structured_output(_VerifierOutput, include_raw=False)

    for clause in clauses:
        clause_id: str = clause["clause_id"]
        articles = retrievals.get(clause_id, [])

        if not articles:
            findings.append(_fallback_finding(clause_id, "aucun article récupéré"))
            continue

        # --- Tentative 1 ---
        output = _call_llm(llm, clause, articles)
        if output is None:
            findings.append(_fallback_finding(clause_id, "erreur LLM (tentative 1)"))
            errors.append(f"Vérificateur: LLM error sur clause '{clause_id}' (T1)")
            continue

        finding_dict = output.model_dump()
        finding_dict["clause_id"] = clause_id

        valid, reason = citation_guard(finding_dict, {clause_id: articles})

        if valid:
            findings.append(_build_finding(clause_id, output, citation_valid=True))
            continue

        logger.warning(
            f"Citation invalide clause '{clause_id}' (T1): {reason}. Retry..."
        )

        # --- Retry (tentative 2) avec feedback ---
        available_ids = ", ".join(a["id"] for a in articles)
        feedback = (
            f"ERREUR: {reason}\n"
            f"IDs disponibles : {available_ids}\n"
            "Tu dois choisir un ID parmi ceux-ci et copier le texte mot-à-mot."
        )
        output2 = _call_llm(llm, clause, articles, extra_feedback=feedback)

        if output2 is not None:
            finding_dict2 = output2.model_dump()
            finding_dict2["clause_id"] = clause_id
            valid2, reason2 = citation_guard(finding_dict2, {clause_id: articles})
            if valid2:
                findings.append(_build_finding(clause_id, output2, citation_valid=True))
                continue
            logger.warning(
                f"Citation encore invalide clause '{clause_id}' (T2): {reason2}. Fallback."
            )

        # --- Fallback final ---
        findings.append(_fallback_finding(clause_id, f"citation invalide après retry: {reason}"))
        errors.append(f"Vérificateur: citation guard échouée clause '{clause_id}'")

    logger.info(
        f"Vérificateur: {len(findings)} findings "
        f"({sum(1 for f in findings if f.get('citation_valid')) } valides)"
    )
    return {"findings": findings, "errors": errors}
