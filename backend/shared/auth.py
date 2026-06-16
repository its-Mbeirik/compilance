"""
JWT utilities and password hashing.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("SECRET_KEY", "conformia-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    )
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ── FastAPI dependencies ───────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Non authentifié")
    try:
        payload = _decode_token(credentials.credentials)
        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Token invalide")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return user


async def require_approved(user: dict = Depends(get_current_user)) -> dict:
    """Admin is always approved; re-check DB for regular users to catch disabled sessions."""
    if user.get("role") == "admin":
        return user
    from db.users_crud import get_user_by_id
    db_user = get_user_by_id(user["sub"])
    if not db_user:
        raise HTTPException(status_code=401, detail="Compte introuvable")
    if db_user["status"] == "disabled":
        raise HTTPException(status_code=403, detail="Votre compte a été désactivé. Contactez l'administrateur.")
    if db_user["status"] != "approved":
        raise HTTPException(status_code=403, detail="Compte en attente d'approbation")
    return user
