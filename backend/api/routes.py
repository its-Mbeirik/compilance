"""
Jalon 4 — Routes FastAPI.
POST  /api/analyses            soumet un contrat → analysis_id (202)
GET   /api/analyses            liste les analyses
GET   /api/analyses/{id}       statut + findings
GET   /api/analyses/{id}/report  téléchargement PDF (ou HTML fallback)
POST  /api/chat/{id}           Q&A contextuelle sur une analyse
"""
import logging
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from api.extract_text import extract_text
from api.report import generate_html, generate_pdf
from db.crud import (
    create_analysis,
    create_contract,
    get_analysis,
    list_analyses,
    update_analysis_done,
    update_analysis_error,
    update_analysis_running,
)

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/conformite_uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


# ---------------------------------------------------------------------------
# Background task — exécute le pipeline LangGraph
# ---------------------------------------------------------------------------

def _run_pipeline_bg(analysis_id: str, contract_text: str, jurisdiction: str) -> None:
    from graph.pipeline import run_pipeline

    try:
        update_analysis_running(analysis_id)
        result = run_pipeline(
            contract_text=contract_text,
            jurisdiction=jurisdiction,
            contract_id=analysis_id,
        )
        update_analysis_done(
            analysis_id,
            findings=result.get("findings", []),
            extracted=result.get("extracted", {}),
        )
        logger.info(f"Pipeline done — analysis {analysis_id}: {len(result.get('findings', []))} findings")
    except Exception as exc:
        logger.error(f"Pipeline error — analysis {analysis_id}: {exc}")
        update_analysis_error(analysis_id, str(exc))


# ---------------------------------------------------------------------------
# POST /api/analyses
# ---------------------------------------------------------------------------

@router.post("/analyses", status_code=202)
async def submit_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    jurisdiction: Literal["ohada", "mauritania_labor"] = Form(...),
):
    """
    Soumet un contrat (PDF/DOCX/TXT) pour analyse.
    Retourne immédiatement analysis_id avec status='pending'.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Format non supporté: {ext}. Acceptés: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 10 MB)")

    # Extrait le texte
    contract_text = extract_text(content, file.filename or "file.txt")
    if not contract_text.strip():
        raise HTTPException(status_code=422, detail="Impossible d'extraire le texte du fichier")

    # Sauvegarde le fichier
    doc_type = "statuts" if jurisdiction == "ohada" else "contrat_travail"
    contract_id = create_contract(doc_type, str(UPLOAD_DIR / (file.filename or "upload")), jurisdiction)
    analysis_id = create_analysis(contract_id)

    save_path = UPLOAD_DIR / f"{analysis_id}{ext}"
    save_path.write_bytes(content)

    background_tasks.add_task(_run_pipeline_bg, analysis_id, contract_text, jurisdiction)

    return {"analysis_id": analysis_id, "status": "pending"}


# ---------------------------------------------------------------------------
# GET /api/analyses
# ---------------------------------------------------------------------------

@router.get("/analyses")
async def get_analyses():
    """Liste les 50 dernières analyses."""
    return list_analyses(limit=50)


# ---------------------------------------------------------------------------
# GET /api/analyses/{id}
# ---------------------------------------------------------------------------

@router.get("/analyses/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Retourne le statut et les findings d'une analyse."""
    rec = get_analysis(analysis_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Analyse '{analysis_id}' introuvable")
    return rec


# ---------------------------------------------------------------------------
# GET /api/analyses/{id}/report
# ---------------------------------------------------------------------------

@router.get("/analyses/{analysis_id}/report")
async def get_report(analysis_id: str, fmt: str = "pdf"):
    """
    Génère et retourne le rapport de conformité.
    ?fmt=pdf  → PDF (défaut)
    ?fmt=html → HTML
    """
    rec = get_analysis(analysis_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Analyse '{analysis_id}' introuvable")
    if rec["status"] != "done":
        raise HTTPException(status_code=409, detail=f"Analyse en cours (status={rec['status']})")

    if fmt == "html":
        html = generate_html(rec)
        return HTMLResponse(content=html)

    # PDF
    try:
        pdf_bytes = generate_pdf(rec)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="rapport_{analysis_id[:8]}.pdf"'
            },
        )
    except RuntimeError as exc:
        logger.warning(f"WeasyPrint indisponible ({exc}), fallback HTML")
        html = generate_html(rec)
        return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# POST /api/chat/{id}
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str


@router.post("/chat/{analysis_id}")
async def chat(analysis_id: str, body: ChatRequest):
    """
    Q&A contextuelle sur une analyse terminée.
    Utilise les findings + articles récupérés comme contexte.
    """
    rec = get_analysis(analysis_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Analyse '{analysis_id}' introuvable")
    if rec["status"] not in ("done", "error"):
        raise HTTPException(status_code=409, detail="Analyse pas encore terminée")

    findings = rec.get("findings", [])
    extracted = rec.get("extracted", {})
    jurisdiction = rec.get("jurisdiction", "")

    context = _build_chat_context(findings, extracted, jurisdiction)
    answer = _ask_llm(body.message, context)

    return {"answer": answer, "analysis_id": analysis_id}


def _build_chat_context(findings: list, extracted: dict, jurisdiction: str) -> str:
    lines = [
        f"Juridiction : {jurisdiction}",
        f"Données extraites : {extracted}",
        "",
        "Findings de conformité :",
    ]
    for f in findings:
        lines.append(
            f"  - Clause {f.get('clause_id')} | {f.get('verdict')} | "
            f"Art. {f.get('cited_article_id')} | {f.get('recommendation', '')}"
        )
    return "\n".join(lines)


def _ask_llm(question: str, context: str) -> str:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage

    system = (
        "Tu es un assistant juridique spécialisé en droit OHADA et droit du travail mauritanien. "
        "Réponds en français, de façon concise et précise, en te basant uniquement sur le contexte fourni."
    )
    prompt = f"Contexte de l'analyse :\n{context}\n\nQuestion : {question}"

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
        temperature=0.3,
        max_tokens=1024,
    )
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=prompt)])
    return response.content
