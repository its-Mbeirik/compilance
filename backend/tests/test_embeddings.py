"""
Test Jalon 1 — BGE-M3 embeddings.
Critère PDF : similarité cosinus > 0.8 sur paraphrases françaises.
Lance avec : pytest tests/test_embeddings.py -v -m slow
Prérequis : pip install sentence-transformers  (télécharge ~2GB)
"""
import numpy as np
import pytest


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


@pytest.fixture(scope="module")
def bge_model():
    pytest.importorskip("sentence_transformers", reason="sentence-transformers non installé")
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("BAAI/bge-m3")


# 10 paires de paraphrases juridiques françaises (OHADA + Code du Travail)
PARAPHRASE_PAIRS = [
    (
        "Le capital social minimum d'une SARL ne peut être inférieur à un million de francs CFA.",
        "Le montant du capital social de la SARL ne peut être inférieur à un million de FCFA.",
    ),
    (
        "La durée de la société ne peut excéder quatre-vingt-dix-neuf ans.",
        "La durée de la société est limitée à quatre-vingt-dix-neuf ans au maximum.",
    ),
    (
        "Le siège social ne peut pas être une simple boîte postale.",
        "Une boîte postale ne peut en aucun cas constituer un siège social.",
    ),
    (
        "Les actions de la SA doivent être libérées d'un quart au moins lors de la souscription.",
        "Lors de la souscription, un quart au moins des actions de la SA doit être libéré.",
    ),
    (
        "La période d'essai ne peut excéder six mois pour les travailleurs.",
        "La période d'essai des travailleurs est limitée à six mois au maximum.",
    ),
    (
        "Le contrat à durée déterminée supérieur à trois mois doit être visé par l'Inspecteur du Travail.",
        "Un CDD de plus de trois mois doit obligatoirement être visé par l'Inspecteur du Travail.",
    ),
    (
        "L'âge minimum légal d'admission à l'emploi est fixé à quatorze ans.",
        "L'âge minimum pour être admis à l'emploi est de quatorze ans.",
    ),
    (
        "Tout travailleur a droit à un congé annuel payé après douze mois de service effectif.",
        "Après douze mois de service effectif, le travailleur a droit à un congé payé annuel.",
    ),
    (
        "Les statuts doivent contenir la dénomination sociale et l'objet social de la société.",
        "La dénomination sociale et l'objet social doivent figurer obligatoirement dans les statuts.",
    ),
    (
        "Le capital social de la société anonyme ne peut être inférieur à dix millions de francs CFA.",
        "La société anonyme doit avoir un capital social d'au moins dix millions de francs CFA.",
    ),
]

# 3 paires NON-paraphrases — la similarité doit rester basse
NON_PARAPHRASE_PAIRS = [
    (
        "Le capital social minimum d'une SARL est de 1 000 000 FCFA.",
        "Les congés payés sont accordés après douze mois de travail.",
    ),
    (
        "L'âge minimum légal est de quatorze ans.",
        "Le capital de la SA ne peut être inférieur à dix millions.",
    ),
]


@pytest.mark.slow
def test_bge_m3_paraphrases(bge_model):
    """Critère Jalon 1 : cosine > 0.8 sur les 10 paires de paraphrases."""
    failed = []
    for s1, s2 in PARAPHRASE_PAIRS:
        e1 = bge_model.encode(s1, normalize_embeddings=True)
        e2 = bge_model.encode(s2, normalize_embeddings=True)
        sim = cosine_similarity(e1, e2)
        if sim <= 0.8:
            failed.append((s1[:50], s2[:50], sim))

    assert not failed, (
        f"{len(failed)}/10 paires sous le seuil 0.8:\n"
        + "\n".join(f"  [{s1}] ~ [{s2}] = {sim:.3f}" for s1, s2, sim in failed)
    )


@pytest.mark.slow
def test_bge_m3_embedding_dimension(bge_model):
    """BGE-M3 doit produire des vecteurs de dimension 1024 (conforme init.sql)."""
    emb = bge_model.encode("Test", normalize_embeddings=True)
    assert emb.shape == (1024,), f"Dimension attendue 1024, obtenue {emb.shape}"


@pytest.mark.slow
def test_bge_m3_non_paraphrases_lower_similarity(bge_model):
    """Les non-paraphrases doivent avoir une similarité inférieure aux paraphrases."""
    paraphrase_sims = []
    for s1, s2 in PARAPHRASE_PAIRS:
        e1 = bge_model.encode(s1, normalize_embeddings=True)
        e2 = bge_model.encode(s2, normalize_embeddings=True)
        paraphrase_sims.append(cosine_similarity(e1, e2))

    non_para_sims = []
    for s1, s2 in NON_PARAPHRASE_PAIRS:
        e1 = bge_model.encode(s1, normalize_embeddings=True)
        e2 = bge_model.encode(s2, normalize_embeddings=True)
        non_para_sims.append(cosine_similarity(e1, e2))

    avg_para = np.mean(paraphrase_sims)
    avg_non_para = np.mean(non_para_sims)
    assert avg_para > avg_non_para, (
        f"Paraphrases ({avg_para:.3f}) devraient être > non-paraphrases ({avg_non_para:.3f})"
    )


@pytest.mark.slow
def test_bge_m3_arabic_french_cross_lingual(bge_model):
    """BGE-M3 supporte français + arabe — vérifie une paire bilingue."""
    fr = "Le capital social minimum est de un million de francs CFA."
    ar = "رأس المال الاجتماعي الأدنى مليون فرنك أفريقي."
    e_fr = bge_model.encode(fr, normalize_embeddings=True)
    e_ar = bge_model.encode(ar, normalize_embeddings=True)
    sim = cosine_similarity(e_fr, e_ar)
    assert sim > 0.6, f"Similarité multilingue fr/ar trop faible: {sim:.3f}"
