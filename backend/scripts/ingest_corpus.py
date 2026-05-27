"""CLI: ingest the legal corpus into pgvector.

Run from the project root:
    python -m backend.scripts.ingest_corpus
or:
    cd backend && python -m scripts.ingest_corpus
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from app.config import settings  # noqa: E402
from app.db.models import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.rag.ingestion import ingest_corpus  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("ingest")


def main():
    parser = argparse.ArgumentParser(description="Ingest legal corpus into pgvector")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=settings.CORPUS_DIR,
        help=f"Corpus directory (default: {settings.CORPUS_DIR})",
    )
    parser.add_argument("--no-replace", action="store_true", help="Skip files already ingested")
    args = parser.parse_args()

    if not args.corpus.exists():
        log.error("Corpus directory not found: %s", args.corpus)
        sys.exit(1)

    log.info("Creating tables if needed...")
    Base.metadata.create_all(bind=engine)

    log.info("Ingesting corpus from %s", args.corpus)
    results = ingest_corpus(args.corpus, replace=not args.no_replace)

    log.info("=" * 60)
    log.info("Ingestion summary:")
    total = 0
    for name, count in results.items():
        flag = "OK" if count >= 0 else "FAIL"
        log.info("  [%s] %s: %d chunks", flag, name, count)
        if count > 0:
            total += count
    log.info("=" * 60)
    log.info("Total chunks ingested: %d", total)


if __name__ == "__main__":
    main()
