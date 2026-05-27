"""Verification agent.

For each clause + its retrieved legal context, asks the LLM whether the clause
is conforming. Produces zero or more `Finding` objects per clause. Also runs a
second pass to detect *missing required clauses* (clauses the law mandates that
do not appear in the contract).
"""

from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import Clause, ConformityState, Finding, LegalCitation
from app.llm.deepseek import get_llm

logger = logging.getLogger(__name__)

VERIFICATION_SYSTEM = """Tu es un juriste expert en droit mauritanien.
On te fournit une clause d'un contrat et des extraits de lois pertinents.

Détermine si la clause est :
1. CONFORME : aucune non-conformité, ne rien retourner
2. NON CONFORME : contredit explicitement une disposition légale
3. RISQUÉE : ambiguë, vague, ou potentiellement non conforme

Pour chaque problème détecté, produis un finding au format JSON :
{
  "severity": "CRITIQUE" | "MAJEURE" | "MINEURE",
  "category": "violation" | "ambiguïté" | "clause_excessive" | "incohérence",
  "description": "explication précise du problème en français",
  "recommendation": "comment corriger la clause",
  "legal_basis": [{"source": "nom de la loi", "article": "Article X", "excerpt": "passage cité"}],
  "confidence": 0.0 à 1.0
}

Réponds UNIQUEMENT avec : {"findings": [...]}. Si la clause est conforme : {"findings": []}.
Pas de markdown, pas de commentaire hors JSON."""

MISSING_SYSTEM = """Tu es un juriste expert en droit mauritanien.
On te fournit la liste des références d'articles présents dans un contrat de type {contract_type}
et des extraits de lois pertinents.

Identifie les clauses OBLIGATOIRES qui DEVRAIENT figurer dans ce type de contrat
mais qui n'apparaissent PAS dans la liste fournie. Pour chacune :
{
  "severity": "CRITIQUE" | "MAJEURE" | "MINEURE",
  "category": "clause_manquante",
  "description": "quelle clause manque et pourquoi elle est obligatoire",
  "recommendation": "rédaction type à insérer",
  "legal_basis": [{"source": "...", "article": "...", "excerpt": "..."}],
  "confidence": 0.0 à 1.0
}

Réponds avec {"findings": [...]}. Pas de markdown."""


def _extract_json(content: str) -> dict | None:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content).strip()
        content = re.sub(r"```$", "", content).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _verify_clause(clause: Clause, citations: list[dict]) -> list[Finding]:
    if not citations:
        return []
    llm = get_llm(temperature=0.0)
    context = "\n\n".join(
        f"[{c.get('source')} — {c.get('article') or 'passage'}]\n{c.get('excerpt')}"
        for c in citations
    )
    user = (
        f"CLAUSE ({clause.ref} — {clause.title}):\n{clause.text}\n\n"
        f"EXTRAITS DE LOI PERTINENTS :\n{context}"
    )
    try:
        response = get_llm(temperature=0.0).invoke(
            [SystemMessage(content=VERIFICATION_SYSTEM), HumanMessage(content=user)]
        )
        data = _extract_json(response.content)
        if not data:
            return []
        findings = []
        for f in data.get("findings", []):
            try:
                f["clause_ref"] = clause.ref
                f["legal_basis"] = [LegalCitation(**lc) for lc in f.get("legal_basis", [])]
                findings.append(Finding(**f))
            except Exception as e:
                logger.warning("Skipping malformed finding: %s", e)
        return findings
    except Exception as e:
        logger.exception("Verification failed for %s: %s", clause.ref, e)
        return []


def _detect_missing(state: ConformityState) -> list[Finding]:
    clauses = state.get("clauses", [])
    retrievals = state.get("retrievals", {})
    contract_type = state.get("contract_type", "contrat")

    refs_present = [c.ref for c in clauses]
    all_citations = []
    for v in retrievals.values():
        all_citations.extend(v[:2])
    if not all_citations:
        return []
    context = "\n\n".join(
        f"[{c.get('source')} — {c.get('article') or 'passage'}]\n{c.get('excerpt')}"
        for c in all_citations[:15]
    )
    user = f"Clauses présentes dans le contrat : {refs_present}\n\nEXTRAITS DE LOI :\n{context}"
    try:
        response = get_llm(temperature=0.0).invoke(
            [
                SystemMessage(content=MISSING_SYSTEM.format(contract_type=contract_type)),
                HumanMessage(content=user),
            ]
        )
        data = _extract_json(response.content)
        if not data:
            return []
        out = []
        for f in data.get("findings", []):
            try:
                f["clause_ref"] = None
                f["legal_basis"] = [LegalCitation(**lc) for lc in f.get("legal_basis", [])]
                out.append(Finding(**f))
            except Exception as e:
                logger.warning("Skipping malformed missing-finding: %s", e)
        return out
    except Exception as e:
        logger.exception("Missing-clause detection failed: %s", e)
        return []


def verification_node(state: ConformityState) -> ConformityState:
    clauses = state.get("clauses", [])
    retrievals = state.get("retrievals", {})

    all_findings: list[Finding] = []
    for clause in clauses:
        citations = retrievals.get(clause.ref, [])
        all_findings.extend(_verify_clause(clause, citations))

    all_findings.extend(_detect_missing(state))

    logger.info("Verification produced %d findings", len(all_findings))
    return {"findings": all_findings}
