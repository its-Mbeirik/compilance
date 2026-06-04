"""
User management routes.

Admin only:
  GET  /api/admin/stats              — counts: pending / users / sub-users
  GET  /api/admin/pending            — list pending registrations
  POST /api/admin/users/{id}/approve — approve a pending user
  POST /api/admin/users/{id}/reject  — reject a pending user
  GET  /api/admin/users              — list all users + sub-users

Validated user only:
  GET  /api/users/sub-users          — list own sub-users
  POST /api/users/sub-users          — create a sub-user (auto-approved)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from shared.auth import require_admin, require_approved, hash_password
from db.users_crud import (
    get_stats, list_pending_users, update_user_status, list_all_users,
    list_sub_users, create_user, get_user_by_email,
)

router = APIRouter()


class CreateSubUserBody(BaseModel):
    name: str
    email: str
    password: str


def _pub(u: dict) -> dict:
    return {
        "id":         u["id"],
        "email":      u["email"],
        "name":       u["name"],
        "role":       u["role"],
        "status":     u["status"],
        "parent_id":  u.get("parent_id"),
        "created_at": u.get("created_at"),
    }


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/stats")
def admin_stats(_: dict = Depends(require_admin)):
    return get_stats()


@router.get("/admin/pending")
def admin_pending(_: dict = Depends(require_admin)):
    return [_pub(u) for u in list_pending_users()]


@router.post("/admin/users/{user_id}/approve")
def admin_approve(user_id: str, _: dict = Depends(require_admin)):
    update_user_status(user_id, "approved")
    return {"message": "Utilisateur approuvé"}


@router.post("/admin/users/{user_id}/reject")
def admin_reject(user_id: str, _: dict = Depends(require_admin)):
    update_user_status(user_id, "rejected")
    return {"message": "Utilisateur rejeté"}


@router.get("/admin/users")
def admin_users(_: dict = Depends(require_admin)):
    return [_pub(u) for u in list_all_users()]


# ── Validated user ────────────────────────────────────────────────────────────

@router.get("/users/sub-users")
def my_sub_users(current: dict = Depends(require_approved)):
    if current["role"] != "user":
        raise HTTPException(403, "Seuls les utilisateurs validés peuvent gérer des sous-utilisateurs")
    return [_pub(u) for u in list_sub_users(current["sub"])]


@router.post("/users/sub-users", status_code=201)
def create_sub_user(body: CreateSubUserBody, current: dict = Depends(require_approved)):
    if current["role"] != "user":
        raise HTTPException(403, "Seuls les utilisateurs validés peuvent créer des sous-utilisateurs")
    if len(body.password) < 6:
        raise HTTPException(400, "Le mot de passe doit comporter au moins 6 caractères")
    if get_user_by_email(body.email):
        raise HTTPException(400, "Cet email est déjà utilisé")
    sub = create_user(
        email=body.email,
        name=body.name.strip(),
        password_hash=hash_password(body.password),
        role="sub_user",
        status="approved",
        parent_id=current["sub"],
    )
    return _pub(sub)
