"""
Ingestion du corpus juridique mauritanien depuis /app/resourse/*.txt
Usage:
    python -m ingestion.ingest_resources            # with BGE-M3 embeddings
    python -m ingestion.ingest_resources --no-embed # text only (fast)
"""
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

RESOURSE_DIR = os.getenv("RESOURSE_DIR", "/app/resourse")

# filename → (code_name, version_date)
RESOURCES = [
    ("01_CODE_DU_TRAVAIL_2004-017_1.txt",       "CODE_TRAVAIL_MR",          "2004-07-06"),
    ("02_CONVENTION_COLLECTIVE_GENERALE.txt",    "CONVENTION_COLLECTIVE_MR", "2024-01-01"),
    ("03_LOI_2022-025_MODIF_CODE_TRAVAIL_1.txt", "LOI_2022_025_MR",          "2022-01-01"),
    ("04_LOI_2024-048_MODIF_CODE_TRAVAIL_1.txt", "LOI_2024_048_MR",          "2024-01-01"),
    ("05_CODE_DU_COMMERCE_2000-05.txt",          "CODE_COMMERCE_MR",         "2000-01-01"),
    ("06_CODE_OBLIGATIONS_ET_CONTRATS.txt",      "COC_MR",                   "1989-01-01"),
    ("07_CONVENTIONS_INTERNATIONALES_OIT.txt",   "CONVENTIONS_OIT_MR",       "2023-01-01"),
    ("08_LOI_2021-005_MODIF_CODE_COMMERCE.txt",  "LOI_2021_005_MR",          "2021-01-01"),
]


def ingest_all(embed: bool = True, batch_size: int = 16, chunk_size: int = 200) -> int:
    from ingestion.parser import segment_by_article
    from ingestion.loader import insert_articles

    if embed:
        from ingestion.embedder import embed_texts

    total = 0

    for filename, code_name, version_date in RESOURCES:
        path = os.path.join(RESOURSE_DIR, filename)
        if not os.path.exists(path):
            logger.warning("Fichier introuvable, ignoré : %s", path)
            continue

        logger.info("━━ %s (%s)", filename, code_name)
        t0 = time.time()

        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except Exception as exc:
            logger.error("Lecture impossible : %s", exc)
            continue

        articles = segment_by_article(text, "mauritania_labor", code_name, version_date)
        logger.info("  %d articles extraits en %.1fs", len(articles), time.time() - t0)

        if not articles:
            logger.warning("  Aucun article détecté — vérifier le format du fichier")
            continue

        if embed:
            logger.info("  Génération embeddings BGE-M3 (chunks de %d)...", chunk_size)
            t1 = time.time()
            n_inserted = 0
            for start in range(0, len(articles), chunk_size):
                chunk = articles[start: start + chunk_size]
                texts = [a.full_text[:2000] for a in chunk]
                embs = embed_texts(texts, batch_size=batch_size)
                n_inserted += insert_articles(chunk, embs)
                logger.info(
                    "  chunk %d-%d → %d insérés",
                    start + 1, min(start + len(chunk), len(articles)), n_inserted,
                )
            logger.info("  Embeddings générés en %.1fs", time.time() - t1)
        else:
            n_inserted = insert_articles(articles, None)

        logger.info("  ✓ %d articles insérés\n", n_inserted)
        total += n_inserted

    logger.info("════ Ingestion terminée : %d articles au total ════", total)
    return total


if __name__ == "__main__":
    embed = "--no-embed" not in sys.argv
    ingest_all(embed=embed)
