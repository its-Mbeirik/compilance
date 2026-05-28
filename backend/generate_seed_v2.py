"""
Generates seed_articles.py from all available Mauritanian law PDFs.
Sources:
  1. Code du Travail complet (Loi N° 2004-017) — F2045592590_MRT68212.pdf   → 451 articles
  2. Code du Commerce (Loi N° 2000-05)                                       → 387 articles
  3. Loi 2021-005 modifiant le Code du Commerce                              → amendments
  4. Code des Obligations et des Contrats (already good — keep as-is via regex)
  5. Convention Collective Générale du Travail (keep as-is)
  6. Conventions Internationales du Travail ratifiées par la Mauritanie      → key articles

Run from backend/ directory:
    python generate_seed_v2.py
"""
import re
import sys
import pdfplumber
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RESOURSE = Path("../resourse")
OUT_FILE = Path("ingestion/seed_articles.py")

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def extract_full_text(pdf_path: Path) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text


def split_by_article(text: str) -> list[tuple[str, str]]:
    """
    Returns list of (article_number, article_text).
    Handles 'Article 1er', 'Article 2', 'Art. 3', etc.
    """
    # Split at every article boundary
    parts = re.split(r"(?m)^(?=Art(?:icle)?\.?\s*\d+\w*\s*[-:.]?\s*\S)", text)
    results = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"Art(?:icle)?\.?\s*(\d+)\w*", part, re.IGNORECASE)
        if not m:
            continue
        num = m.group(1)
        results.append((num, part))
    return results


def clean(text: str) -> str:
    """Remove excessive whitespace while preserving readability."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def py_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


# ---------------------------------------------------------------------------
# 1. Code du Travail complet
# ---------------------------------------------------------------------------
print("Extracting Code du Travail...", flush=True)
ct_text = extract_full_text(RESOURSE / "F2045592590_MRT68212.pdf")
ct_articles = split_by_article(ct_text)
print(f"  → {len(ct_articles)} articles found")

# ---------------------------------------------------------------------------
# 2. Code du Commerce
# ---------------------------------------------------------------------------
print("Extracting Code du Commerce...", flush=True)
cc_text = extract_full_text(RESOURSE / "Loi n° 2000-05 du 15 mars 2000 portant Code du Commerce..pdf")
cc_articles = split_by_article(cc_text)
print(f"  → {len(cc_articles)} articles found")

# ---------------------------------------------------------------------------
# 3. Loi 2021-005 modifiant le Code du Commerce
# ---------------------------------------------------------------------------
print("Extracting Loi 2021-005 (Code Commerce amendments)...", flush=True)
try:
    amend_text = extract_full_text(RESOURSE / "F272633922_MRT-113004.pdf")
    amend_articles = split_by_article(amend_text)
    print(f"  → {len(amend_articles)} amendment articles found")
except Exception as e:
    print(f"  WARNING: {e}")
    amend_articles = []

# ---------------------------------------------------------------------------
# 4. Code des Obligations et des Contrats — re-extract from the PDF
# ---------------------------------------------------------------------------
print("Extracting Code des Obligations et Contrats...", flush=True)
coc_pdf = RESOURSE / "code-des-obligations-et-des-contrats_ordonnance-nc2b0-89-126-modific3a9e-par-la-loi-nc2b0-2001-31-du-7-fc3a9vrier-2001.pdf"
coc_text = extract_full_text(coc_pdf)
coc_articles = split_by_article(coc_text)
print(f"  → {len(coc_articles)} articles found")

# ---------------------------------------------------------------------------
# 5. Convention Collective Générale du Travail — re-extract
# ---------------------------------------------------------------------------
print("Extracting Convention Collective...", flush=True)
conv_text = extract_full_text(RESOURSE / "Convention Collective Générale du Travail.pdf")
conv_articles = split_by_article(conv_text)
print(f"  → {len(conv_articles)} articles found")

# ---------------------------------------------------------------------------
# 6. Conventions Internationales du Travail ratifiées par la Mauritanie
# ---------------------------------------------------------------------------
print("Extracting Conventions Internationales du Travail...", flush=True)
intl_text = extract_full_text(RESOURSE / "LES CONVENTIONS INTERNATIONALES - Mauritanie.pdf")
# For ILO conventions we only take the first ~200 articles to stay focused
intl_articles_raw = split_by_article(intl_text)
# Deduplicate by number, keep first occurrence (fundamental conventions come first)
seen_intl: set[str] = set()
intl_articles: list[tuple[str, str]] = []
for num, txt in intl_articles_raw:
    if num not in seen_intl and int(num) <= 50:  # keep only short articles (≤50)
        seen_intl.add(num)
        intl_articles.append((num, txt))
print(f"  → {len(intl_articles)} key articles selected")

# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def write_section(
    fh,
    var_name: str,
    articles: list[tuple[str, str]],
    jurisdiction: str,
    code_name: str,
    version_date: str,
    prefix: str = "",
) -> None:
    """Write one list of RawArticle entries."""
    fh.write(f"\n{var_name}: list[RawArticle] = [\n")
    seen: set[str] = set()
    for num, text in articles:
        art_id = f"{prefix}{num}" if prefix else num
        if art_id in seen:
            continue
        seen.add(art_id)
        cleaned = py_escape(clean(text))
        fh.write(
            f'    RawArticle(\n'
            f'        article_number={repr(art_id)},\n'
            f'        full_text="{cleaned}",\n'
            f'        hierarchy_path="",\n'
            f'        jurisdiction={repr(jurisdiction)},\n'
            f'        code_name={repr(code_name)},\n'
            f'        version_date={repr(version_date)},\n'
            f'    ),\n'
        )
    fh.write("]\n")


print(f"\nWriting {OUT_FILE} ...", flush=True)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write('"""\n')
    f.write("Ressources juridiques mauritaniennes — générées automatiquement depuis les PDFs officiels.\n")
    f.write("Sources :\n")
    f.write("  - Code du Travail complet (Loi N° 2004-017, mod. 2009-027)\n")
    f.write("  - Code du Commerce (Loi N° 2000-05, mod. 2021-005)\n")
    f.write("  - Code des Obligations et des Contrats (Ordonnance n° 89-126, mod. Loi n° 2001-31)\n")
    f.write("  - Convention Collective Générale du Travail (UNICEMA / UTM)\n")
    f.write("  - Conventions Internationales du Travail ratifiées par la Mauritanie (DGT/DRDS/2023)\n")
    f.write('"""\n')
    f.write("from ingestion.parser import RawArticle\n")

    write_section(f, "CODE_TRAVAIL_ARTICLES",   ct_articles,    "mauritania_labor", "CODE_TRAVAIL_MR",    "2009-01-01")
    write_section(f, "CODE_COMMERCE_ARTICLES",  cc_articles,    "mauritania_labor", "CODE_COMMERCE_MR",   "2000-01-18")
    write_section(f, "CODE_COMMERCE_AMEND_ARTICLES", amend_articles, "mauritania_labor", "CODE_COMMERCE_MR", "2021-02-15", prefix="AME-")
    write_section(f, "COC_ARTICLES",            coc_articles,   "mauritania_labor", "COC_MR",             "2001-02-07")
    write_section(f, "CONVENTION_COLLECTIVE_ARTICLES", conv_articles, "mauritania_labor", "CC_GENERAL_MR", "2000-01-01")
    write_section(f, "CONVENTIONS_INTL_ARTICLES", intl_articles, "mauritania_labor", "CONV_INTL_OIT",     "2023-01-01", prefix="OIT-")

    # Combined list
    f.write("\nALL_ARTICLES: list[RawArticle] = (\n")
    f.write("    CODE_TRAVAIL_ARTICLES\n")
    f.write("    + CODE_COMMERCE_ARTICLES\n")
    f.write("    + CODE_COMMERCE_AMEND_ARTICLES\n")
    f.write("    + COC_ARTICLES\n")
    f.write("    + CONVENTION_COLLECTIVE_ARTICLES\n")
    f.write("    + CONVENTIONS_INTL_ARTICLES\n")
    f.write(")\n")

print("Done.")
