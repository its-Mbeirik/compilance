"""
CRUD helpers pour les tables contracts et analyses.
"""
import json
import uuid
from typing import Optional

from db.database import get_connection


def create_contract(
    doc_type: str,
    source_path: str,
    jurisdiction: str,
    user_id: Optional[str] = None,
) -> str:
    cid = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO contracts (id, doc_type, source_path, jurisdiction, user_id) VALUES (%s,%s,%s,%s,%s)",
                (cid, doc_type, source_path, jurisdiction, user_id),
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


def get_analysis(
    analysis_id: str,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None,
) -> Optional[dict]:
    """
    Returns the analysis if it exists and the caller is allowed to see it.
    - admin   : unrestricted
    - user    : own analyses + sub-users' analyses
    - sub_user: own analyses only
    - None    : unrestricted (internal calls from background tasks)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            base = """
                SELECT a.id, a.status, a.findings_json, a.error_log,
                       a.created_at, a.finished_at,
                       c.jurisdiction, c.doc_type, c.source_path, c.user_id
                FROM analyses a
                JOIN contracts c ON c.id = a.contract_id
                WHERE a.id = %s
            """
            if user_role == "admin" or user_id is None:
                cur.execute(base, (analysis_id,))
            elif user_role == "user":
                cur.execute(
                    base + " AND (c.user_id = %s OR c.user_id IN (SELECT id FROM users WHERE parent_id = %s))",
                    (analysis_id, user_id, user_id),
                )
            else:  # sub_user
                cur.execute(base + " AND c.user_id = %s", (analysis_id, user_id))
            row = cur.fetchone()

    if not row:
        return None
    payload = row[2] or {}
    return {
        "id":           str(row[0]),
        "status":       row[1],
        "findings":     payload.get("findings", []),
        "extracted":    payload.get("extracted", {}),
        "error_log":    row[3],
        "created_at":   row[4].isoformat() if row[4] else None,
        "finished_at":  row[5].isoformat() if row[5] else None,
        "jurisdiction": row[6],
        "doc_type":     row[7],
        "source_path":  row[8],
    }


def list_analyses(
    limit: int = 50,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None,
) -> list[dict]:
    """
    Returns analyses visible to the caller:
    - admin      : all analyses
    - user       : own + sub-users' analyses
    - sub_user   : own analyses only
    """
    SELECT = """
        SELECT a.id, a.status, a.created_at, a.finished_at, c.jurisdiction, c.doc_type
        FROM analyses a
        JOIN contracts c ON c.id = a.contract_id
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if user_role == "admin" or user_id is None:
                cur.execute(SELECT + " ORDER BY a.created_at DESC LIMIT %s", (limit,))
            elif user_role == "user":
                cur.execute(
                    SELECT + """
                        WHERE c.user_id = %s
                           OR c.user_id IN (SELECT id FROM users WHERE parent_id = %s)
                        ORDER BY a.created_at DESC LIMIT %s
                    """,
                    (user_id, user_id, limit),
                )
            else:  # sub_user
                cur.execute(
                    SELECT + " WHERE c.user_id = %s ORDER BY a.created_at DESC LIMIT %s",
                    (user_id, limit),
                )
            rows = cur.fetchall()

    return [
        {
            "id":           str(r[0]),
            "analysis_id":  str(r[0]),
            "status":       r[1],
            "created_at":   r[2].isoformat() if r[2] else None,
            "finished_at":  r[3].isoformat() if r[3] else None,
            "jurisdiction": r[4],
            "doc_type":     r[5],
        }
        for r in rows
    ]
