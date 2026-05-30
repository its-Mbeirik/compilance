"""
CRUD helpers pour les tables contracts et analyses.
"""
import json
import uuid
from typing import Optional

from db.database import get_connection


def create_contract(doc_type: str, source_path: str, jurisdiction: str) -> str:
    cid = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO contracts (id, doc_type, source_path, jurisdiction) VALUES (%s,%s,%s,%s)",
                (cid, doc_type, source_path, jurisdiction),
            )
    return cid


def create_analysis(contract_id: str) -> str:
    aid = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO analyses (id, contract_id, status) VALUES (%s,%s,'pending')",
                (aid, contract_id),
            )
    return aid


def update_analysis_running(analysis_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE analyses SET status='running' WHERE id=%s", (analysis_id,))


def update_analysis_done(analysis_id: str, findings: list, extracted: dict) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE analyses
                   SET status='done', findings_json=%s::jsonb, finished_at=NOW()
                   WHERE id=%s""",
                (json.dumps({"findings": findings, "extracted": extracted}), analysis_id),
            )


def update_analysis_error(analysis_id: str, error: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE analyses SET status='error', error_log=%s, finished_at=NOW() WHERE id=%s",
                (error, analysis_id),
            )


def get_analysis(analysis_id: str) -> Optional[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT a.id, a.status, a.findings_json, a.error_log,
                          a.created_at, a.finished_at,
                          c.jurisdiction, c.doc_type, c.source_path
                   FROM analyses a
                   JOIN contracts c ON c.id = a.contract_id
                   WHERE a.id = %s""",
                (analysis_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    payload = row[2] or {}
    return {
        "id": str(row[0]),
        "status": row[1],
        "findings": payload.get("findings", []),
        "extracted": payload.get("extracted", {}),
        "error_log": row[3],
        "created_at": row[4].isoformat() if row[4] else None,
        "finished_at": row[5].isoformat() if row[5] else None,
        "jurisdiction": row[6],
        "doc_type": row[7],
        "source_path": row[8],
    }


def list_analyses(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT a.id, a.status, a.created_at, a.finished_at,
                          c.jurisdiction, c.doc_type
                   FROM analyses a
                   JOIN contracts c ON c.id = a.contract_id
                   ORDER BY a.created_at DESC LIMIT %s""",
                (limit,),
            )
            rows = cur.fetchall()
    return [
        {
            "id": str(r[0]),
            "analysis_id": str(r[0]),
            "status": r[1],
            "created_at": r[2].isoformat() if r[2] else None,
            "finished_at": r[3].isoformat() if r[3] else None,
            "jurisdiction": r[4], "doc_type": r[5],
        }
        for r in rows
    ]
