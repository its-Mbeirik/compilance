"""
Jalon 2 — Script principal d'ingestion du corpus juridique.
Usage:
    python -m ingestion.ingest --pdf path/to/auscgie.pdf --jurisdiction ohada \
                               --code AUSCGIE --version-date 2014-05-05

    python -m ingestion.ingest --seed           # insère les articles de seed_articles.py
    python -m ingestion.ingest --seed --embed   # seed + génère les vrais embeddings BGE-M3
"""
import argparse
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def ingest_from_pdf(
    pdf_path: str,
    jurisdiction: str,
    code_name: str,
    version_date: str | None = None,
    language: str = "fr",
    batch_size: int = 32,
    embed: bool = True,
) -> int:
    """
    Pipeline complet : PDF → articles → embeddings → pgvector.
    Retourne le nombre d'articles indexés.
    """
    from ingestion.parser import parse_pdf
    from ingestion.embedder import embed_texts
    from ingestion.loader import insert_articles

    logger.info(f"Parsing {pdf_path} ...")
    t0 = time.time()
    articles = parse_pdf(pdf_path, jurisdiction, code_name, version_date, language)
    logger.info(f"  {len(articles)} articles extraits en {time.time()-t0:.1f}s")

    embeddings = None
    if embed:
        logger.info(f"Génération des embeddings BGE-M3 (batchs de {batch_size}) ...")
        t1 = time.time()
        texts = [a.full_text for a in articles]
        embeddings = embed_texts(texts, batch_size=batch_size)
        logger.info(f"  Embeddings générés en {time.time()-t1:.1f}s")

    logger.info("Insertion dans pgvector ...")
    t2 = time.time()
    count = insert_articles(articles, embeddings)
    logger.info(f"  {count} articles insérés en {time.time()-t2:.1f}s")

    return count


def ingest_seed(embed: bool = True, batch_size: int = 16, chunk_size: int = 200) -> int:
    """
    Insère les articles de référence (seed_articles.py) avec ou sans embeddings.
    Traite par chunks de `chunk_size` pour éviter les OOM sur CPU.
    Ignore les articles déjà présents en base (idempotent).
    """
    from ingestion.seed_articles import ALL_ARTICLES
    from ingestion.loader import insert_articles, count_articles

    # Skip articles already in DB (allows resume after crash)
    already = count_articles()
    articles_to_process = ALL_ARTICLES[already:]
    if already > 0:
        logger.info(f"Reprise : {already} articles déjà en base, {len(articles_to_process)} restants")

    if not articles_to_process:
        logger.info("Tous les articles sont déjà en base.")
        return already

    total_inserted = 0

    if not embed:
        total_inserted = insert_articles(articles_to_process, None)
    else:
        from ingestion.embedder import embed_texts
        total = len(articles_to_process)
        logger.info(f"Génération des embeddings pour {total} articles (chunks de {chunk_size}) ...")

        for start in range(0, total, chunk_size):
            chunk = articles_to_process[start: start + chunk_size]
            texts = [a.full_text[:2000] for a in chunk]  # truncate to avoid OOM on long articles
            logger.info(f"  Chunk {start//chunk_size + 1}: articles {start+1}–{min(start+len(chunk), total)}/{total}")
            embs = embed_texts(texts, batch_size=batch_size)
            n = insert_articles(chunk, embs)
            total_inserted += n
            logger.info(f"  → {n} insérés (total so far: {already + total_inserted})")

    logger.info(
        f"Seed terminé : {already + total_inserted} articles au total "
        f"({'avec' if embed else 'sans'} embeddings)"
    )
    return already + total_inserted


def print_stats() -> None:
    """Affiche les statistiques d'indexation."""
    from ingestion.loader import count_articles
    total = count_articles()
    labor = count_articles("mauritania_labor")
    logger.info(f"Stats legal_articles : total={total} | mauritania_labor={labor}")
    if total > 0:
        logger.info(
            "  Sources : Code du Travail + COC + Convention Collective"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Ingestion du corpus juridique OHADA / Code du Travail MR"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf", type=str, help="Chemin vers le PDF à ingérer")
    group.add_argument("--seed", action="store_true",
                       help="Insère les articles de référence (seed_articles.py)")

    parser.add_argument("--jurisdiction", choices=["ohada", "mauritania_labor"],
                        help="Juridiction (requis avec --pdf)")
    parser.add_argument("--code", type=str,
                        help="Nom du code, ex: AUSCGIE ou CODE_TRAVAIL_MR")
    parser.add_argument("--version-date", type=str, default=None,
                        help="Date de version ISO, ex: 2014-05-05")
    parser.add_argument("--language", type=str, default="fr",
                        choices=["fr", "ar"])
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--no-embed", action="store_true",
                        help="Insère sans générer les embeddings")
    parser.add_argument("--stats", action="store_true",
                        help="Affiche les statistiques après ingestion")

    args = parser.parse_args()
    embed = not args.no_embed

    if args.seed:
        ingest_seed(embed=embed, batch_size=args.batch_size)
    else:
        if not args.jurisdiction or not args.code:
            parser.error("--jurisdiction et --code sont requis avec --pdf")
        if not Path(args.pdf).exists():
            logger.error(f"Fichier introuvable : {args.pdf}")
            sys.exit(1)
        ingest_from_pdf(
            pdf_path=args.pdf,
            jurisdiction=args.jurisdiction,
            code_name=args.code,
            version_date=args.version_date,
            language=args.language,
            batch_size=args.batch_size,
            embed=embed,
        )

    if args.stats:
        print_stats()


if __name__ == "__main__":
    main()
