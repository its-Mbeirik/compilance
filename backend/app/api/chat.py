"""Interactive chat endpoint — Q&A over the legal corpus + optionally a contract."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Contract, Finding as FindingRow
from app.db.session import get_db
from app.llm.deepseek import get_llm
from app.rag.retriever import format_for_prompt, retrieve

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    contract_id: str | None = None
    k: int = 5


class ChatSource(BaseModel):
    source: str
    article: str | None
    excerpt: str
    score: float


class ChatResponse(BaseModel):
    reply: str
    sources: list[ChatSource]
    contract_context: dict | None = None


SYSTEM_PROMPT = """Tu es un assistant juridique expert en droit mauritanien
(Code du Travail, Code de Commerce, Code des Obligations et des Contrats,
Convention Collective Générale du Travail).

Tu réponds aux questions des notaires, juristes et particuliers sur la conformité
contractuelle. Tes réponses doivent être :
- Précises et fondées sur les extraits de loi fournis
- En français, dans un registre professionnel
- Avec des références aux articles quand pertinent
- Honnêtes : si la réponse n'est pas dans le contexte fourni, dis-le explicitement

Si un contrat spécifique est mentionné dans le contexte, tu peux te référer à ses
clauses et aux non-conformités déjà détectées."""


def _build_contract_context(db: Session, contract_id: str) -> dict | None:
    contract = db.get(Contract, contract_id)
    if not contract:
        return None
    findings = db.execute(
        select(FindingRow).where(FindingRow.contract_id == contract_id)
    ).scalars().all()
    return {
        "filename": contract.filename,
        "contract_type": contract.contract_type,
        "status": contract.status,
        "raw_text_preview": contract.raw_text[:4000],
        "findings_summary": [
            {
                "clause_ref": f.clause_ref,
                "severity": f.severity,
                "description": f.description[:300],
            }
            for f in findings
        ],
    }


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.messages:
        raise HTTPException(400, "messages cannot be empty")
    last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
    if not last_user:
        raise HTTPException(400, "no user message found")

    try:
        hits = retrieve(last_user.content, k=req.k)
    except Exception as e:
        logger.exception("Retrieval failed: %s", e)
        hits = []

    legal_context = format_for_prompt(hits)

    contract_ctx = None
    contract_block = ""
    if req.contract_id:
        contract_ctx = _build_contract_context(db, req.contract_id)
        if contract_ctx:
            findings_str = "\n".join(
                f"  - [{f['severity']}] {f['clause_ref']}: {f['description']}"
                for f in contract_ctx["findings_summary"]
            ) or "  (aucune non-conformité détectée)"
            contract_block = (
                f"\n\n=== CONTRAT EN COURS D'ANALYSE ===\n"
                f"Fichier : {contract_ctx['filename']}\n"
                f"Type : {contract_ctx['contract_type']}\n"
                f"Extrait du contrat :\n{contract_ctx['raw_text_preview']}\n\n"
                f"Non-conformités détectées :\n{findings_str}\n"
                f"=== FIN DU CONTRAT ===\n"
            )

    augmented = (
        f"{contract_block}\n\n"
        f"=== EXTRAITS LÉGAUX PERTINENTS ===\n{legal_context}\n=== FIN EXTRAITS ===\n\n"
        f"QUESTION DE L'UTILISATEUR :\n{last_user.content}"
    )

    history_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in req.messages[:-1]:
        if m.role == "user":
            history_messages.append(HumanMessage(content=m.content))
    history_messages.append(HumanMessage(content=augmented))

    try:
        llm = get_llm(temperature=0.2)
        response = llm.invoke(history_messages)
        reply = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        logger.exception("LLM call failed: %s", e)
        raise HTTPException(502, f"LLM error: {e}") from e

    return ChatResponse(
        reply=reply,
        sources=[
            ChatSource(
                source=h.source_title,
                article=h.article_ref,
                excerpt=h.content[:600],
                score=round(h.score, 4),
            )
            for h in hits
        ],
        contract_context=contract_ctx,
    )
