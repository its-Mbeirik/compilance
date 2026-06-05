"""
Authentication routes.

POST /api/auth/register          — public: create a pending account + send verification email
POST /api/auth/login             — public: returns JWT
GET  /api/auth/verify-email      — public: verify email via token in query param
POST /api/auth/forgot-password   — public: send password-reset email
POST /api/auth/reset-password    — public: reset password with token
GET  /api/auth/me                — authenticated: current user profile
PUT  /api/auth/profile           — authenticated: update name/email
PUT  /api/auth/password          — authenticated: change password
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from shared.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)
from db.users_crud import (
    create_user, get_user_by_email, get_user_by_id,
    update_profile, update_password, mark_email_verified,
)
from db.tokens_crud import create_token, get_valid_token, delete_token

router = APIRouter()


# ── Request bodies ─────────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    name:     str
    email:    str
    password: str


class LoginBody(BaseModel):
    email:    str
    password: str


class ProfileBody(BaseModel):
    name:  str
    email: str


class PasswordBody(BaseModel):
    current_password: str
    new_password:     str


class ForgotPasswordBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token:        str
    new_password: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def _pub(u: dict) -> dict:
    return {
        "id":             u["id"],
        "email":          u["email"],
        "name":           u["name"],
        "role":           u["role"],
        "status":         u["status"],
        "parent_id":      u.get("parent_id"),
        "email_verified": u.get("email_verified", False),
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
def register(body: RegisterBody):
    if len(body.password) < 6:
        raise HTTPException(400, "Le mot de passe doit comporter au moins 6 caractères")
    if get_user_by_email(body.email):
        raise HTTPException(400, "Cet email est déjà utilisé")
    user = create_user(
        email=body.email,
        name=body.name.strip(),
        password_hash=hash_password(body.password),
        role="user",
        status="pending",
    )
    token = create_token(user["id"], "email_verification", expire_hours=24)
    from shared.email import send_verification_email
    send_verification_email(body.email, body.name.strip(), token)  # runs in daemon thread
    return {
        "message": "Compte créé. Vérifiez votre email puis attendez l'approbation d'un administrateur.",
        "id": user["id"],
    }


@router.post("/login")
def login(body: LoginBody):
    user = get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Email ou mot de passe incorrect")
    token = create_access_token({
        "sub":            user["id"],
        "email":          user["email"],
        "name":           user["name"],
        "role":           user["role"],
        "status":         user["status"],
        "parent_id":      user.get("parent_id"),
        "email_verified": user.get("email_verified", False),
    })
    return {"token": token, "user": _pub(user)}


@router.get("/verify-email")
def verify_email(token: str = Query(...)):
    record = get_valid_token(token, "email_verification")
    if not record:
        raise HTTPException(400, "Lien de vérification invalide ou expiré")
    mark_email_verified(record["user_id"])
    delete_token(token)
    return {"message": "Adresse email vérifiée avec succès"}


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordBody):
    user = get_user_by_email(body.email)
    if user:
        token = create_token(user["id"], "password_reset", expire_hours=1)
        from shared.email import send_reset_email
        send_reset_email(body.email, user["name"], token)  # runs in daemon thread
    # Always return success to avoid user-enumeration attacks
    return {"message": "Si cet email est associé à un compte, un lien de réinitialisation vous a été envoyé."}


@router.post("/reset-password")
def reset_password(body: ResetPasswordBody):
    if len(body.new_password) < 6:
        raise HTTPException(400, "Le mot de passe doit comporter au moins 6 caractères")
    record = get_valid_token(body.token, "password_reset")
    if not record:
        raise HTTPException(400, "Lien de réinitialisation invalide ou expiré")
    update_password(record["user_id"], hash_password(body.new_password))
    delete_token(body.token)
    return {"message": "Mot de passe réinitialisé avec succès"}


@router.get("/me")
def me(current: dict = Depends(get_current_user)):
    user = get_user_by_id(current["sub"])
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    return _pub(user)


@router.put("/profile")
def update_my_profile(body: ProfileBody, current: dict = Depends(get_current_user)):
    existing = get_user_by_email(body.email)
    if existing and existing["id"] != current["sub"]:
        raise HTTPException(400, "Cet email est déjà utilisé par un autre compte")
    user = update_profile(current["sub"], body.name.strip(), body.email)
    return _pub(user)


@router.put("/password")
def change_my_password(body: PasswordBody, current: dict = Depends(get_current_user)):
    if len(body.new_password) < 6:
        raise HTTPException(400, "Le nouveau mot de passe doit comporter au moins 6 caractères")
    user = get_user_by_id(current["sub"])
    if not verify_password(body.current_password, user["password_hash"]):
        raise HTTPException(400, "Mot de passe actuel incorrect")
    update_password(current["sub"], hash_password(body.new_password))
    return {"message": "Mot de passe mis à jour avec succès"}
