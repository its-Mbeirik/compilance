"""
Garde-fou de citation déterministe (~30 lignes).
Rejette toute citation d'article non présent dans l'ensemble récupéré
et toute citation textuelle non littéralement présente dans l'article cité.
Cf. PDF section 3.3.3 Listing 3.
"""
from typing import Any


def citation_guard(
    finding: dict[str, Any],
    retrievals: dict[str, list[dict[str, Any]]],
) -> tuple[bool, str]:
    """
    Retourne (True, "OK") si la citation est valide.
    Retourne (False, raison) si le LLM a halluciné l'article ou le texte.

    Args:
        finding:    dict avec 'clause_id', 'cited_article_id', 'quoted_text'
        retrievals: {clause_id: [{"id": ..., "text": ...}, ...]}  (top-5 du reranker)
    """
    clause_id = finding["clause_id"]

    if clause_id not in retrievals:
        return False, f"clause_id '{clause_id}' absent des retrievals"

    allowed_ids = {a["id"] for a in retrievals[clause_id]}
    if finding["cited_article_id"] not in allowed_ids:
        return False, f"ID '{finding['cited_article_id']}' inventé (non dans top-5)"

    article = next(
        a for a in retrievals[clause_id]
        if a["id"] == finding["cited_article_id"]
    )
    if finding["quoted_text"] not in article["text"]:
        return False, "Citation textuelle non trouvée littéralement dans l'article"

    return True, "OK"
