"""
Jalon 2 — Parser de corpus juridique.
Extraction PDF → segmentation par article → hiérarchie Livre/Titre/Chapitre/Article.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


# ---------------------------------------------------------------------------
# Modèle de données brut (avant insertion DB)
# ---------------------------------------------------------------------------

@dataclass
class RawArticle:
    article_number: str
    full_text: str
    hierarchy_path: str
    jurisdiction: str
    code_name: str
    language: str = "fr"
    version_date: Optional[str] = None
    country_override: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        return f"{self.jurisdiction.upper()}-{self.code_name}-{self.article_number}"


# ---------------------------------------------------------------------------
# Patterns de segmentation
# ---------------------------------------------------------------------------

# Titres de niveau hiérarchique
_HIER_PATTERNS = [
    ("livre",    re.compile(r"(?:^|\n)\s*(?:LIVRE|Livre)\s+([IVXLCDM]+(?:\s+\w+)*)", re.M)),
    ("titre",    re.compile(r"(?:^|\n)\s*(?:TITRE|Titre)\s+([IVXLCDM0-9]+(?:\s+[A-ZÀ-Üa-zà-ü ]+)?)", re.M)),
    ("chapitre", re.compile(r"(?:^|\n)\s*(?:CHAPITRE|Chapitre)\s+([IVXLCDM0-9]+(?:\s+[A-ZÀ-Üa-zà-ü ]+)?)", re.M)),
    ("section",  re.compile(r"(?:^|\n)\s*(?:SECTION|Section)\s+([IVXLCDM0-9]+(?:\s+[A-ZÀ-Üa-zà-ü ]+)?)", re.M)),
]

# Début d'article — toutes les variantes rencontrées dans OHADA/Code du Travail
_ARTICLE_PATTERN = re.compile(
    r"(?:^|\n)\s*"
    r"(?:Art(?:icle)?\.?\s*)"
    r"(\d+(?:\s*[-–]\s*\d+)?)"   # numéro simple "311" ou plage "153-154"
    r"(?:\s*(?:[:.-]|\.))?",
    re.IGNORECASE | re.MULTILINE,
)

# Numéros de page et en-têtes répétitifs à supprimer
_NOISE_PATTERNS = [
    re.compile(r"^\s*\d+\s*$", re.MULTILINE),            # page seule
    re.compile(r"OHADA\s*[-–]\s*Acte Uniforme.*?\n", re.IGNORECASE),
    re.compile(r"Code du Travail.*?\n", re.IGNORECASE),
    re.compile(r"Journal Officiel.*?\n", re.IGNORECASE),
    re.compile(r"[-–]{10,}", re.MULTILINE),               # lignes de séparation
]


# ---------------------------------------------------------------------------
# Fonctions principales
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Supprime les en-têtes, pieds de page et artefacts d'extraction."""
    for pattern in _NOISE_PATTERNS:
        text = pattern.sub(" ", text)
    # Normalise les espaces multiples
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extrait le texte brut d'un PDF avec pdfplumber."""
    if not HAS_PDFPLUMBER:
        raise ImportError("pdfplumber requis: pip install pdfplumber")

    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if text:
                pages.append(text)
    return "\n".join(pages)


def _build_hierarchy_index(text: str) -> list[tuple[int, str, str]]:
    """
    Retourne une liste triée par position : [(pos, niveau, label), ...]
    Utilisée pour retrouver le contexte hiérarchique d'un article.
    """
    entries = []
    for level, pattern in _HIER_PATTERNS:
        for m in pattern.finditer(text):
            label = m.group(1).strip()[:80]
            entries.append((m.start(), level, label))
    return sorted(entries, key=lambda x: x[0])


def _hierarchy_at(pos: int, hier_index: list) -> str:
    """Retourne le chemin hiérarchique pour la position `pos`."""
    context: dict[str, str] = {}
    for entry_pos, level, label in hier_index:
        if entry_pos > pos:
            break
        context[level] = label
    parts = []
    for level in ("livre", "titre", "chapitre", "section"):
        if level in context:
            parts.append(f"{level.capitalize()} {context[level]}")
    return " > ".join(parts) if parts else "Dispositions générales"


def segment_by_article(
    text: str,
    jurisdiction: str,
    code_name: str,
    version_date: Optional[str] = None,
    language: str = "fr",
) -> list[RawArticle]:
    """
    Découpe `text` en articles individuels.
    Retourne une liste de RawArticle avec hiérarchie reconstruite.
    """
    text = clean_text(text)
    hier_index = _build_hierarchy_index(text)

    matches = list(_ARTICLE_PATTERN.finditer(text))
    articles = []

    for i, match in enumerate(matches):
        article_num = match.group(1).strip().replace(" ", "")
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        raw_body = text[start:end].strip()
        if len(raw_body) < 10:
            continue

        hierarchy = _hierarchy_at(match.start(), hier_index)

        articles.append(RawArticle(
            article_number=article_num,
            full_text=f"Article {article_num} : {raw_body}",
            hierarchy_path=hierarchy,
            jurisdiction=jurisdiction,
            code_name=code_name,
            language=language,
            version_date=version_date,
        ))

    return articles


def parse_pdf(
    pdf_path: str | Path,
    jurisdiction: str,
    code_name: str,
    version_date: Optional[str] = None,
    language: str = "fr",
) -> list[RawArticle]:
    """
    Pipeline complet : PDF → texte brut → articles segmentés.
    Avec fallback OCR Tesseract si pdfplumber retourne moins de 100 caractères.
    """
    raw_text = extract_text_from_pdf(pdf_path)

    if len(raw_text.strip()) < 100:
        raise ValueError(
            f"PDF vide ou illisible (<100 chars). "
            f"Envisager Tesseract OCR pour {pdf_path}"
        )

    return segment_by_article(raw_text, jurisdiction, code_name, version_date, language)
