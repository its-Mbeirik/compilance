"""
CRUD helpers for the users table.
"""
import uuid
from typing import Optional

from db.database import get_connection


def _row(r) -> Optional[dict]:
    if not r:
        return None
    return {
        "id":             str(r[0]),
        "email":          r[1],
        "name":           r[2],
        "password_hash":  r[3],
        "role":           r[4],
        "status":         r[5],
        "parent_id":      str(r[6]) if r[6] else None,
        "created_at":     r[7].isoformat() if r[7] else None,
        "updated_at":     r[8].isoformat() if r[8] else None,
        "email_verified": bool(r[9]) if len(r) > 9 else False,
    }


def create_user(
    email: str,
    name: str,
    password_hash: str,
    role: str = "user",
    status: str = "pending",
    parent_id: Optional[str] = None,
) -> dict:
    uid = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users (id, email, name, password_hash, role, status, parent_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (uid, email, name, password_hash, role, status, parent_id),
            )
            return _row(cur.fetchone())


def get_user_by_email(email: str) -> Optional[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            return _row(cur.fetchone())


def get_user_by_id(user_id: str) -> Optional[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return _row(cur.fetchone())


def list_pending_users() -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE role = 'user' AND status = 'pending' ORDER BY created_at DESC"
            )
            return [_row(r) for r in cur.fetchall()]


def list_all_users() -> list:
    """All users and sub-users (no admins)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE role != 'admin' ORDER BY role, created_at DESC"
            )
            return [_row(r) for r in cur.fetchall()]


def update_user_status(user_id: str, status: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, user_id),
            )


def list_sub_users(parent_id: str) -> list:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE parent_id = %s ORDER BY created_at DESC",
                (parent_id,),
            )
            return [_row(r) for r in cur.fetchall()]


def update_profile(user_id: str, name: str, email: str) -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET name = %s, email = %s, updated_at = NOW() WHERE id = %s RETURNING *",
                (name, email, user_id),
            )
            return _row(cur.fetchone())


def update_password(user_id: str, password_hash: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
                (password_hash, user_id),
            )


def get_stats() -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'user' AND status = 'pending'")
            pending = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
            total_users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'sub_user'")
            total_sub_users = cur.fetchone()[0]
    return {"pending": pending, "total_users": total_users, "total_sub_users": total_sub_users}


def mark_email_verified(user_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET email_verified = TRUE, updated_at = NOW() WHERE id = %s",
                (user_id,),
            )
