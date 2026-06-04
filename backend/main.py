import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Assistant de Conformité Contractuelle",
    description="Système agentique de vérification — Code du Travail, COC et Conventions Mauritaniennes",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def seed_admin():
    """Create the admin account on first startup if it does not exist."""
    try:
        from db.users_crud import get_user_by_email, create_user
        from shared.auth import hash_password

        email = os.getenv("ADMIN_EMAIL", "admin@conformia.mr")
        password = os.getenv("ADMIN_PASSWORD", "Admin1234!")

        if not get_user_by_email(email):
            create_user(
                email=email,
                name="Administrateur",
                password_hash=hash_password(password),
                role="admin",
                status="approved",
            )
            logger.info("Admin account created: %s", email)
    except Exception as exc:
        logger.warning("Admin seed skipped (DB not ready?): %s", exc)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}


from api.routes import router as analysis_router
from api.auth_routes import router as auth_router
from api.users_routes import router as users_router

app.include_router(analysis_router, prefix="/api")
app.include_router(auth_router,     prefix="/api/auth")
app.include_router(users_router,    prefix="/api")
