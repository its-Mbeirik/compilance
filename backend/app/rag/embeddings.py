"""Local embeddings using BAAI/bge-m3 via sentence-transformers.

bge-m3 is multilingual (FR/AR/EN), 1024-dim, strong on long passages — well-suited
for Mauritanian legal text. First call downloads the model (~2GB) to the HF cache.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from sentence_transformers import SentenceTransformer  # noqa: E402

from app.config import settings  # noqa: E402

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    logger.info("Loading embedding model %s ...", settings.EMBEDDING_MODEL)
    model = SentenceTransformer(
        settings.EMBEDDING_MODEL,
        cache_folder=str(settings.EMBEDDINGS_CACHE_DIR),
    )
    return model


def embed_texts(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    if not texts:
        return []
    model = get_embedder()
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
