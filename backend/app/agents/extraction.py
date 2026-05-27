"""Extraction agent.

Parses a contract's raw text into structured `Clause` objects. Uses the LLM
with a strict JSON output instruction; falls back to a regex split on Article
markers if JSON parsing fails.
"""

from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import Clause, ConformityState
from app.llm.deepseek import get_llm

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM = """Tu es un expert juridique mauritanien spécialisé dans l'analyse de contrats.
Ta tâche est d'extraire de manière exhaustive toutes les clauses d'un contrat sous forme structurée.

Pour chaque clause/article :
- ref : référence exacte (ex. "Article 7", "Titre III - Article 12")
- title : titre court de la clause (ex. "Capital social")
- text : texte verbatim de la clause, complet
- topic : thème juridique principal (ex. "capital", "cession des parts", "gérance", "rémunération")

Réponds UNIQUEMENT avec un JSON valide : {"clauses": [...]}. Pas de commentaire, pas de markdown."""


_ARTICLE_RE = re.compile(r"(?im)^\s*#{0,4}\s*(article\s+\d+[^\n]*)$")


def _fallback_split(text: str) -> list[Clause]:
    matches = list(_ARTICLE_RE.finditer(text))
    if not matches:
        return [Clause(ref="Document", text=text[:8000])]
    clauses = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        header = m.group(1).strip()
        clauses.append(Clause(ref=header.split("—")[0].strip(), title=header, text=body))
    return clauses


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


def extraction_node(state: ConformityState) -> ConformityState:
    text = state.get("contract_text", "")
    if not text.strip():
        return {"clauses": [], "error": "empty contract_text"}

    llm = get_llm(temperature=0.0)
    truncated = text[:30000]
    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM),
        HumanMessage(content=f"Contrat à analyser :\n\n{truncated}"),
    ]

    try:
        response = llm.invoke(messages)
        data = _extract_json(response.content)
        if data and isinstance(data.get("clauses"), list):
            clauses = [Clause(**c) for c in data["clauses"]]
            logger.info("Extracted %d clauses via LLM", len(clauses))
            return {"clauses": clauses}
    except Exception as e:
        logger.warning("LLM extraction failed (%s), falling back to regex split", e)

    clauses = _fallback_split(text)
    logger.info("Extracted %d clauses via fallback", len(clauses))
    return {"clauses": clauses}
