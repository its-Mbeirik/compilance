"""
Connexion PostgreSQL + pgvector.
Utilisé par les tests, l'ingestion, et les nœuds LangGraph.
"""
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import psycopg
from pgvector.psycopg import register_vector

# Charge .env depuis backend/ ou la racine du projet si présent
try:
    from dotenv import load_dotenv
    for _candidate in [
        Path(__file__).parent.parent / ".env",      # backend/.env
        Path(__file__).parent.parent.parent / ".env",  # project root .env
    ]:
        if _candidate.exists():
            load_dotenv(_candidate, override=False)
            break
except ImportError:
    pass

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://conformite:conformite_secret@localhost:5433/conformite_db",
)


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Context manager renvoyant une connexion avec pgvector enregistré."""
    conn = psycopg.connect(DATABASE_URL)
    register_vector(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_pgvector() -> bool:
    """Retourne True si l'extension pgvector est chargée."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            return cur.fetchone() is not None


def check_tables() -> list[str]:
    """Retourne la liste des tables existantes dans le schéma public."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )
            return [row[0] for row in cur.fetchall()]
