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
async def ensure_tables():
    """Create tables added after initial DB setup (idempotent)."""
    try:
        from db.database import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_action_logs (
                        id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        admin_id       UUID NOT NULL REFERENCES users(id),
                        admin_name     TEXT NOT NULL,
                        target_user_id UUID NOT NULL REFERENCES users(id),
                        target_name    TEXT NOT NULL,
                        action         TEXT NOT NULL,
                        old_status     TEXT,
                        new_status     TEXT NOT NULL,
                        created_at     TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS admin_logs_created_idx ON admin_action_logs (created_at DESC)"
                )
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        analysis_id   UUID,
                        user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        original_name TEXT NOT NULL,
                        storage_path  TEXT NOT NULL,
                        mime_type     TEXT NOT NULL DEFAULT 'application/octet-stream',
                        size_bytes    BIGINT NOT NULL DEFAULT 0,
                        file_type     TEXT NOT NULL DEFAULT 'upload',
                        created_at    TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS files_analysis_idx ON files (analysis_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS files_user_idx ON files (user_id)")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS archives (
                        id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        analysis_id       UUID,
                        user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        title             TEXT,
                        doc_type          TEXT,
                        employer_name     TEXT,
                        original_file_id  UUID,
                        corrected_file_id UUID,
                        archived_at       TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS archives_user_idx ON archives (user_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS archives_analysis_idx ON archives (analysis_id)")
                # Idempotent column addition for existing databases
                cur.execute("ALTER TABLE archives ADD COLUMN IF NOT EXISTS employer_name TEXT")
    except Exception as exc:
        logger.warning("ensure_tables skipped: %s", exc)


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
