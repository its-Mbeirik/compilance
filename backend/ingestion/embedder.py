"""
Jalon 2 — Génération d'embeddings BGE-M3.
Traitement par batchs de 32, normalisation L2, dimension 1024.
Modèle : BAAI/bge-m3 (MIT licence, local, multilingue fr+ar).
"""
import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_MODEL = None  # singleton chargé paresseusement


def load_model(model_name: str = "BAAI/bge-m3"):
    """Charge BGE-M3 une seule fois (singleton)."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Chargement du modèle {model_name} ...")
        _MODEL = SentenceTransformer(model_name)
        logger.info("Modèle chargé.")
    except ImportError:
        raise ImportError("sentence-transformers requis: pip install sentence-transformers")

    return _MODEL


def embed_texts(
    texts: list[str],
    batch_size: int = 32,
    model_name: str = "BAAI/bge-m3",
    show_progress: bool = True,
) -> np.ndarray:
    """
    Génère les embeddings pour une liste de textes.

    Args:
        texts:        liste de chaînes à encoder
        batch_size:   taille des batchs (32 selon PDF)
        model_name:   modèle HuggingFace à utiliser
        show_progress: affiche une barre de progression

    Returns:
        np.ndarray de shape (len(texts), 1024), normalisés L2
    """
    model = load_model(model_name)

    all_embeddings = []
    total = len(texts)

    for start in range(0, total, batch_size):
        batch = texts[start : start + batch_size]
        embeddings = model.encode(
            batch,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        all_embeddings.append(embeddings)

        if show_progress:
            done = min(start + batch_size, total)
            logger.info(f"  Embeddings : {done}/{total} ({100*done//total}%)")

    result = np.vstack(all_embeddings)
    assert result.shape == (len(texts), 1024), (
        f"Dimension attendue (n, 1024), obtenue {result.shape}"
    )
    return result


def embed_query(query: str, model_name: str = "BAAI/bge-m3") -> np.ndarray:
    """Encode une requête unique — utilisée au moment de la recherche."""
    return embed_texts([query], batch_size=1, model_name=model_name, show_progress=False)[0]
