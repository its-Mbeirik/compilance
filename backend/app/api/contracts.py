"""HTTP endpoints for uploading + verifying a contract."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.graph import run_verification
from app.config import settings
from app.db.models import Contract, Finding as FindingRow
from app.db.session import get_db, session_scope
from app.llm.deepseek import get_llm
from app.utils.docloader import load_document
from app.utils.md_to_docx import markdown_to_docx_bytes

router = APIRouter(prefix="/contracts", tags=["contracts"])
logger = logging.getLogger(__name__)


class FindingOut(BaseModel):
    id: str
    severity: str
    category: str
    clause_ref: str | None
    description: str
    recommendation: str | None
    legal_basis: list[dict]
    confidence: float


class ContractOut(BaseModel):
    id: str
    filename: str
    contract_type: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    findings: list[FindingOut]
    report: str | None = None


def _save_upload(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "").suffix.lower() or ".bin"
    dest = settings.UPLOADS_DIR / f"{uuid4().hex}{suffix}"
    dest.write_bytes(upload.file.read())
    return dest


def _run_pipeline(contract_id: str, text: str, contract_type: str) -> None:
    """Background task: run the agent graph and persist findings + report."""
    try:
        result = run_verification(text, contract_type=contract_type, contract_id=contract_id)
        with session_scope() as db:
            contract = db.get(Contract, contract_id)
            if not contract:
                logger.error("Contract %s vanished mid-run", contract_id)
                return
            for f in result.get("findings", []):
                db.add(
                    FindingRow(
                        contract_id=contract_id,
                        severity=f.severity,
                        category=f.category,
                        clause_ref=f.clause_ref,
                        description=f.description,
                        recommendation=f.recommendation,
                        legal_basis=[lc.model_dump() for lc in f.legal_basis],
                        confidence=f.confidence,
                    )
                )
            contract.status = "completed"
            contract.completed_at = datetime.now(timezone.utc)
            contract.contract_metadata = {**(contract.contract_metadata or {}), "report": result.get("report", "")}
    except Exception as e:
        logger.exception("Pipeline failed for contract %s: %s", contract_id, e)
        with session_scope() as db:
            contract = db.get(Contract, contract_id)
            if contract:
                contract.status = "failed"
                contract.contract_metadata = {**(contract.contract_metadata or {}), "error": str(e)}


@router.post("/verify", response_model=ContractOut)
def verify_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    contract_type: str = Form("statuts"),
    db: Session = Depends(get_db),
):
    saved = _save_upload(file)
    try:
        text = load_document(saved)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse document: {e}") from e
    if not text.strip():
        raise HTTPException(status_code=400, detail="Document is empty after parsing")

    contract = Contract(
        filename=file.filename or saved.name,
        contract_type=contract_type,
        raw_text=text,
        status="processing",
        contract_metadata={"saved_path": str(saved)},
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    background_tasks.add_task(_run_pipeline, contract.id, text, contract_type)

    return ContractOut(
        id=contract.id,
        filename=contract.filename,
        contract_type=contract.contract_type,
        status=contract.status,
        created_at=contract.created_at,
        completed_at=contract.completed_at,
        findings=[],
        report=None,
    )


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")
    rows = db.execute(
        select(FindingRow).where(FindingRow.contract_id == contract_id)
    ).scalars().all()
    return ContractOut(
        id=contract.id,
        filename=contract.filename,
        contract_type=contract.contract_type,
        status=contract.status,
        created_at=contract.created_at,
        completed_at=contract.completed_at,
        findings=[
            FindingOut(
                id=r.id,
                severity=r.severity,
                category=r.category,
                clause_ref=r.clause_ref,
                description=r.description,
                recommendation=r.recommendation,
                legal_basis=r.legal_basis or [],
                confidence=r.confidence,
            )
            for r in rows
        ],
        report=(contract.contract_metadata or {}).get("report"),
    )


@router.get("/", response_model=list[ContractOut])
def list_contracts(db: Session = Depends(get_db)):
    contracts = db.execute(select(Contract).order_by(Contract.created_at.desc())).scalars().all()
    return [
        ContractOut(
            id=c.id,
            filename=c.filename,
            contract_type=c.contract_type,
            status=c.status,
            created_at=c.created_at,
            completed_at=c.completed_at,
            findings=[],
            report=None,
        )
        for c in contracts
    ]


def _safe_filename(name: str, ext: str) -> str:
    stem = Path(name).stem
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in stem).strip()
    return f"{safe or 'document'}.{ext}"


@router.get("/{contract_id}/download")
def download_report(
    contract_id: str,
    format: str = Query("md", pattern="^(md|docx)$"),
    db: Session = Depends(get_db),
):
    """Download the compliance report as Markdown or DOCX."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")
    if contract.status != "completed":
        raise HTTPException(409, f"Contract not ready (status: {contract.status})")

    report_md = (contract.contract_metadata or {}).get("report") or ""
    if not report_md.strip():
        raise HTTPException(404, "No report available for this contract")

    base = _safe_filename(contract.filename, format)
    fname = f"rapport_conformite_{base}"

    if format == "md":
        return Response(
            content=report_md.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )

    blob = markdown_to_docx_bytes(report_md, title=f"Rapport de conformité — {contract.filename}")
    return Response(
        content=blob,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


CORRECTION_SYSTEM = """Tu es un juriste expert en droit mauritanien.
On te fournit un contrat original ET la liste des non-conformités détectées.

Ta tâche : produire une **version corrigée** du contrat qui applique TOUTES les
recommandations, tout en conservant la structure et le style notarial original.

Règles strictes :
- Reproduis intégralement le contrat avec les corrections appliquées.
- Garde la numérotation et la structure des articles.
- Reformule les clauses non conformes selon les recommandations.
- Ajoute les clauses manquantes signalées comme telles.
- N'ajoute AUCUN commentaire, aucune note, aucune justification dans le document.
- Format : Markdown propre (titres, articles, listes). Ce sera converti en DOCX."""


@router.post("/{contract_id}/corrected")
def generate_corrected(
    contract_id: str,
    format: str = Query("docx", pattern="^(md|docx)$"),
    db: Session = Depends(get_db),
):
    """Generate a corrected version of the contract via LLM, downloadable."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")
    if contract.status != "completed":
        raise HTTPException(409, f"Contract not ready (status: {contract.status})")

    findings = db.execute(
        select(FindingRow).where(FindingRow.contract_id == contract_id)
    ).scalars().all()

    if not findings:
        # Nothing to correct; just return the original.
        original = contract.raw_text
        base = _safe_filename(contract.filename, format)
        fname = f"contrat_revu_{base}"
        if format == "md":
            return Response(content=original.encode("utf-8"), media_type="text/markdown",
                            headers={"Content-Disposition": f'attachment; filename="{fname}"'})
        blob = markdown_to_docx_bytes(original, title=f"Contrat revu — {contract.filename}")
        return Response(content=blob,
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        headers={"Content-Disposition": f'attachment; filename="{fname}"'})

    findings_block = "\n".join(
        f"- [{f.severity}] {f.clause_ref or '(clause manquante)'} — {f.description}\n"
        f"  Recommandation : {f.recommendation or '(à formuler)'}"
        for f in findings
    )

    truncated_text = contract.raw_text[:60000]
    user_msg = (
        f"=== CONTRAT ORIGINAL ===\n{truncated_text}\n\n"
        f"=== NON-CONFORMITÉS DÉTECTÉES ===\n{findings_block}\n\n"
        f"Produis maintenant la version corrigée du contrat en Markdown. "
        f"Ne réponds RIEN d'autre que le contrat lui-même."
    )

    try:
        llm = get_llm(temperature=0.0)
        response = llm.invoke([
            SystemMessage(content=CORRECTION_SYSTEM),
            HumanMessage(content=user_msg),
        ])
        corrected_md = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        logger.exception("LLM correction failed: %s", e)
        raise HTTPException(502, f"LLM error: {e}") from e

    base = _safe_filename(contract.filename, format)
    fname = f"contrat_corrige_{base}"

    if format == "md":
        return Response(
            content=corrected_md.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )

    blob = markdown_to_docx_bytes(corrected_md, title=f"Contrat corrigé — {contract.filename}")
    return Response(
        content=blob,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
