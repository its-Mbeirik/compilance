"""
Script d'extraction : génère ingestion/seed_articles.py à partir des PDFs mauritaniens.
Usage : python generate_seed.py
"""
import pdfplumber
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")


# ── Helpers ────────────────────────────────────────────────────────────────

def read_pdf(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            t = p.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages.append(t)
    return "\n".join(pages)


def extract_articles(full_text):
    pat = re.compile(
        r"(?m)^(?:Art(?:icle)?\.?\s*(?:1er|Premier|\d+))\s*[\.\-:]?\s*(.+?)"
        r"(?=\n(?:Art(?:icle)?\.?\s*(?:1er|\d+))|\Z)",
        re.DOTALL,
    )
    num_pat = re.compile(r"^(?:Art(?:icle)?\.?\s*)(1er|Premier|\d+)", re.IGNORECASE)
    articles = {}
    for m in pat.finditer(full_text):
        nm = num_pat.match(m.group(0).split("\n")[0])
        if not nm:
            continue
        raw = nm.group(1)
        num = 1 if raw.lower() in ("1er", "premier") else int(raw)
        body = " ".join(m.group(0).split())[:700]
        if len(body) > 40:
            articles[num] = body
    return articles


# ── Hierarchy maps ─────────────────────────────────────────────────────────

CT_HIER = {
    range(1, 4):    "Dispositions Préliminaires",
    range(4, 65):   "Livre I > Titre I : Contrat de Travail",
    range(65, 101): "Livre I > Titre II-VI : Relations Collectives",
    range(101, 153):"Livre II : L'Entreprise",
    range(153, 170):"Livre III > Titre I : Travail des Femmes et Enfants",
    range(170, 178):"Livre III > Titre II : Durée du Travail",
    range(178, 191):"Livre III > Titre III : Congés Payés",
    range(191, 238):"Livre III > Titre IV : Salaires",
    range(238, 264):"Livre III > Titre V : Hygiène et Sécurité",
    range(264, 292):"Livre IV : Groupements Professionnels",
    range(292, 400):"Livre V : Différends du Travail",
    range(400, 452):"Livre VI : Dispositions Pénales et Finales",
}

COC_HIER = {
    range(1, 22):   "Livre Premier : Dispositions Générales",
    range(22, 100): "Livre Premier : Des Obligations en Général",
    range(100, 135):"Livre Premier : Extinction et Transfert des Obligations",
    range(135, 178):"Livre Premier : Preuves",
    range(178, 280):"Livre II : Des Contrats Spéciaux",
    range(280, 400):"Livre II : Vente et Échange",
    range(400, 600):"Livre II : Autres Contrats",
}


def ct_hier(n):
    for r, h in CT_HIER.items():
        if n in r:
            return h
    return "Dispositions Diverses"


def coc_hier(n):
    for r, h in COC_HIER.items():
        if n in r:
            return h
    return "Dispositions Générales"


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


# ── Load PDFs ──────────────────────────────────────────────────────────────

RESOURSE = "../resourse"

print("Reading Code du Travail...")
arts_ct = extract_articles(read_pdf(f"{RESOURSE}/code_du_travail_de_rim.pdf"))

print("Reading COC...")
arts_coc = extract_articles(read_pdf(
    f"{RESOURSE}/code-des-obligations-et-des-contrats_ordonnance-nc2b0-89-126"
    f"-modific3a9e-par-la-loi-nc2b0-2001-31-du-7-fc3a9vrier-2001.pdf"
))

print("Reading Convention Collective...")
arts_cc = extract_articles(read_pdf(
    f"{RESOURSE}/Convention Collective Générale du Travail.pdf"
))

print(f"CT={len(arts_ct)}  COC={len(arts_coc)}  CC={len(arts_cc)}")

# ── Target sets ────────────────────────────────────────────────────────────

CT_TARGETS = (
    list(range(1, 65))       # Dispositions préliminaires + tout le contrat de travail
    + list(range(107, 115))  # Pouvoir disciplinaire
    + list(range(153, 168))  # Travail femmes/enfants
    + list(range(170, 215))  # Durée travail, congés, salaires
    + list(range(238, 254))  # Hygiène et sécurité
)

COC_TARGETS = (
    list(range(1, 12))       # Dispositions générales
    + list(range(15, 32))    # Capacité
    + list(range(35, 115))   # Formation, consentement, nullité, effets
    + list(range(114, 135))  # Responsabilité civile, prescription
    + list(range(174, 200))  # Contrats spéciaux
)

CC_TARGETS = list(range(1, 72))  # Tous les 71 articles

# ── Build output ───────────────────────────────────────────────────────────

lines = []
lines.append('"""')
lines.append("Ressources juridiques mauritaniennes — générées automatiquement depuis les PDFs officiels.")
lines.append("Sources :")
lines.append("  - Code du Travail (Loi N° 2004-017, modifiée par 2009-027)")
lines.append("  - Code des Obligations et des Contrats (Ordonnance n° 89-126, mod. Loi n° 2001-31)")
lines.append("  - Convention Collective Générale du Travail (UNICEMA / UTM)")
lines.append('"""')
lines.append("from ingestion.parser import RawArticle")
lines.append("")

# ── CT ─────────────────────────────────────────────────────────────────────
lines.append("# " + "-" * 75)
lines.append("# Code du Travail  —  Loi N° 2004-017 modifiée par 2009-027")
lines.append('# jurisdiction="mauritania_labor"  |  code_name="CODE_TRAVAIL_MR"')
lines.append("# " + "-" * 75)
lines.append("CODE_TRAVAIL_ARTICLES: list[RawArticle] = [")
ct_written = 0
for n in sorted(set(CT_TARGETS) & set(arts_ct.keys())):
    txt = esc(arts_ct[n])
    hier = ct_hier(n)
    lines.append("    RawArticle(")
    lines.append(f'        article_number="{n}",')
    lines.append(f'        full_text="{txt}",')
    lines.append(f'        hierarchy_path="{hier}",')
    lines.append('        jurisdiction="mauritania_labor",')
    lines.append('        code_name="CODE_TRAVAIL_MR",')
    lines.append('        version_date="2009-01-01",')
    lines.append("    ),")
    ct_written += 1
lines.append("]")
lines.append("")

# ── COC ────────────────────────────────────────────────────────────────────
lines.append("# " + "-" * 75)
lines.append("# Code des Obligations et des Contrats  —  Ordonnance n° 89-126")
lines.append('# jurisdiction="mauritania_labor"  |  code_name="COC_MR"')
lines.append("# " + "-" * 75)
lines.append("COC_ARTICLES: list[RawArticle] = [")
coc_written = 0
for n in sorted(set(COC_TARGETS) & set(arts_coc.keys())):
    txt = esc(arts_coc[n])
    hier = coc_hier(n)
    lines.append("    RawArticle(")
    lines.append(f'        article_number="COC-{n}",')
    lines.append(f'        full_text="{txt}",')
    lines.append(f'        hierarchy_path="{hier}",')
    lines.append('        jurisdiction="mauritania_labor",')
    lines.append('        code_name="COC_MR",')
    lines.append('        version_date="2001-02-07",')
    lines.append("    ),")
    coc_written += 1
lines.append("]")
lines.append("")

# ── CC ─────────────────────────────────────────────────────────────────────
lines.append("# " + "-" * 75)
lines.append("# Convention Collective Générale du Travail  (UNICEMA / UTM)")
lines.append('# jurisdiction="mauritania_labor"  |  code_name="CONV_COLL_MR"')
lines.append("# " + "-" * 75)
lines.append("CONVENTION_COLLECTIVE_ARTICLES: list[RawArticle] = [")
cc_written = 0
for n in sorted(set(CC_TARGETS) & set(arts_cc.keys())):
    txt = esc(arts_cc[n])
    lines.append("    RawArticle(")
    lines.append(f'        article_number="CC-{n}",')
    lines.append(f'        full_text="{txt}",')
    lines.append('        hierarchy_path="Convention Collective Générale du Travail",')
    lines.append('        jurisdiction="mauritania_labor",')
    lines.append('        code_name="CONV_COLL_MR",')
    lines.append('        version_date="2000-01-01",')
    lines.append("    ),")
    cc_written += 1
lines.append("]")
lines.append("")
lines.append("ALL_ARTICLES = CODE_TRAVAIL_ARTICLES + COC_ARTICLES + CONVENTION_COLLECTIVE_ARTICLES")
lines.append("")

# ── Write file ─────────────────────────────────────────────────────────────
out_path = "ingestion/seed_articles.py"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

total = ct_written + coc_written + cc_written
print(f"\nWrote {out_path}")
print(f"  Code du Travail      : {ct_written} articles")
print(f"  COC                  : {coc_written} articles")
print(f"  Convention Collective: {cc_written} articles")
print(f"  TOTAL                : {total} articles")
