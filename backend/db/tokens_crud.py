"""
CRUD helpers for the user_tokens table.
Used for email verification and password reset flows.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from db.database import get_connection


def create_token(user_id: str, token_type: str, expire_hours: int = 24) -> str:
    """Create a new token, replacing any existing token of the same type for this user."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM user_tokens WHERE user_id = %s AND type = %s",
                (user_id, token_type),
            )
            cur.execute(
                "INSERT INTO user_tokens (user_id, token, type, expires_at) VALUES (%s, %s, %s, %s)",
                (user_id, token, token_type, expires_at),
            )
    return token


def get_valid_token(token: str, token_type: str) -> Optional[dict]:
    """Return token record if it exists and has not expired, else None."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, expires_at FROM user_tokens WHERE token = %s AND type = %s",
                (token, token_type),
            )
            row = cur.fetchone()
    if not row:
        return None
    expires_at = row[1]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        delete_token(token)
        return None
    return {"user_id": str(row[0]), "expires_at": expires_at}


def delete_token(token: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_tokens WHERE token = %s", (token,))
