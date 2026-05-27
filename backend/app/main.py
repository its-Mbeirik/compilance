"""FastAPI entrypoint."""

from __future__ import annotations

import os

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import logging  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api import chat, contracts, corpus  # noqa: E402
from app.config import settings  # noqa: E402

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Système Agentique de Vérification de Conformité Contractuelle",
    version="0.1.0",
    description="Multi-agent LangGraph system for verifying Mauritanian contracts against law.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{settings.FRONTEND_PORT}", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def warmup_embedder():
    """Load the embedding model at startup so the first request is fast."""
    import time
    from app.rag.embeddings import embed_query
    log = logging.getLogger("startup")
    log.info("Warming up embedder...")
    t0 = time.time()
    embed_query("warmup")
    log.info("Embedder warm in %.1fs", time.time() - t0)


@app.get("/health")
def health():
    return {"status": "ok", "model": settings.DEEPSEEK_MODEL, "embedding": settings.EMBEDDING_MODEL}


app.include_router(contracts.router)
app.include_router(corpus.router)
app.include_router(chat.router)
