"""Ingest the legal corpus into pgvector.

Pipeline: walk the corpus directory → load each document → chunk it → embed →
upsert into `legal_chunks`. Idempotent at the (source_file, chunk_index) level.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import delete, select
from tqdm import tqdm

from app.db.models import LegalChunk
from app.db.session import session_scope
from app.rag.chunker import chunk_legal_text
from app.rag.embeddings import embed_texts
from app.utils.docloader import load_document

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def ingest_file(path: Path, *, replace: bool = True) -> int:
    """Ingest one file. Returns the number of chunks stored."""
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.warning("Skipping unsupported file: %s", path)
        return 0

    logger.info("Loading %s", path.name)
    text = load_document(path)
    if not text.strip():
        logger.warning("Empty content for %s", path.name)
        return 0

    chunks = chunk_legal_text(text)
    if not chunks:
        return 0

    logger.info("Embedding %d chunks from %s", len(chunks), path.name)
    vectors = embed_texts([c.content for c in chunks], batch_size=16)

    with session_scope() as db:
        if replace:
            db.execute(delete(LegalChunk).where(LegalChunk.source_file == str(path.name)))

        for chunk, vector in zip(chunks, vectors, strict=True):
            db.add(
                LegalChunk(
                    source_file=path.name,
                    source_title=path.stem,
                    article_ref=chunk.article_ref,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    embedding=vector,
                    chunk_metadata=chunk.extra,
                )
            )
    return len(chunks)


def ingest_corpus(corpus_dir: Path, *, replace: bool = True) -> dict[str, int]:
    """Ingest every supported file under `corpus_dir`. Returns {filename: chunks}."""
    files = sorted(p for p in corpus_dir.rglob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    logger.info("Found %d files in %s", len(files), corpus_dir)
    results: dict[str, int] = {}
    for path in tqdm(files, desc="Ingesting corpus"):
        try:
            results[path.name] = ingest_file(path, replace=replace)
        except Exception as e:
            logger.exception("Failed to ingest %s: %s", path, e)
            results[path.name] = -1
    return results


def corpus_stats() -> dict:
    with session_scope() as db:
        total = db.scalar(select(LegalChunk).with_only_columns(LegalChunk.id).order_by(None))
        count = db.execute(select(LegalChunk).with_only_columns(LegalChunk.id)).all()
    return {"total_chunks": len(count)}
