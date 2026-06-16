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

from shared.auth import require_admin, require_approved, hash_password, verify_password
from db.users_crud import (
    get_stats, list_pending_users, update_user_status, list_all_users,
    list_sub_users, create_user, get_user_by_email, get_user_by_id,
    log_admin_action, get_admin_logs,
)

router = APIRouter()


class CreateSubUserBody(BaseModel):
    name:            str
    email:           str
    password:        str
    parent_password: str


class SetStatusBody(BaseModel):
    action: str  # 'disable' | 'enable'


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


@router.patch("/admin/users/{user_id}/status")
def admin_set_status(user_id: str, body: SetStatusBody, current: dict = Depends(require_admin)):
    if body.action not in ("disable", "enable"):
        raise HTTPException(400, "Action invalide : utilisez 'disable' ou 'enable'")
    target = get_user_by_id(user_id)
    if not target:
        raise HTTPException(404, "Utilisateur introuvable")
    new_status = "disabled" if body.action == "disable" else "approved"
    old_status = target["status"]
    update_user_status(user_id, new_status)
    log_admin_action(
        admin_id=current["sub"],
        admin_name=current["name"],
        target_user_id=user_id,
        target_name=target["name"],
        action=body.action,
        old_status=old_status,
        new_status=new_status,
    )
    return {"message": "Statut mis à jour", "new_status": new_status}


@router.get("/admin/logs")
def admin_get_logs(_: dict = Depends(require_admin)):
    return get_admin_logs()


# ── Validated user ────────────────────────────────────────────────────────────

@router.get("/users/sub-users")
def my_sub_users(current: dict = Depends(require_approved)):
    if current["role"] != "user":
        raise HTTPException(403, "Seuls les utilisateurs validés peuvent gérer des assistants")
    return [_pub(u) for u in list_sub_users(current["sub"])]


@router.post("/users/sub-users", status_code=201)
def create_sub_user(body: CreateSubUserBody, current: dict = Depends(require_approved)):
    if current["role"] != "user":
        raise HTTPException(403, "Seuls les utilisateurs validés peuvent créer des assistants")

    # Verify the parent's own password before allowing sub-user creation
    parent = get_user_by_id(current["sub"])
    if not parent or not verify_password(body.parent_password, parent["password_hash"]):
        raise HTTPException(401, "Mot de passe incorrect")

    if len(body.password) < 6:
        raise HTTPException(400, "Le mot de passe de l'assistant doit comporter au moins 6 caractères")
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
