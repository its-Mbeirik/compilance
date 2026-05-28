"""
Génération de documents Word (.docx) pour contrats mauritaniens.
  - generate_contract_docx(description) → bytes  : nouveau contrat via LLM
  - correct_contract_docx(analysis_rec) → bytes  : contrat corrigé via LLM + findings
"""
import io
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ── Formatting helpers ──────────────────────────────────────────────────────

def _set_font(run, size_pt: int = 11, bold: bool = False):
    run.font.name = "Calibri"
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    # embed font name in rPr for compatibility
    r = run._r
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Calibri")
    rFonts.set(qn("w:hAnsi"), "Calibri")
    rPr.insert(0, rFonts)


def _add_title(doc: Document, text: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text.upper())
    _set_font(run, 14, bold=True)
    p.paragraph_format.space_after = Pt(12)


def _add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    _set_font(run, 12 if level == 1 else 11, bold=True)
    if level == 1:
        run.font.color.rgb = RGBColor(0, 0, 0)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)


def _add_body(doc: Document, text: str):
    p = doc.add_paragraph()
    run = p.add_run(text)
    _set_font(run, 11)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.first_line_indent = Inches(0.3)


def _add_article(doc: Document, number: str, text: str):
    p = doc.add_paragraph()
    run_num = p.add_run(f"Article {number} — ")
    _set_font(run_num, 11, bold=True)
    run_body = p.add_run(text)
    _set_font(run_body, 11)
    p.paragraph_format.space_after = Pt(6)


def _build_docx(title: str, llm_text: str) -> bytes:
    """
    Parse LLM output and build a properly formatted .docx.
    Supported markers in llm_text:
      ## Section title       → bold heading
      ### Sub-heading        → smaller bold
      Art. N / Article N     → article style
      - bullet               → list item
      plain text             → body paragraph
    """
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin   = Inches(1.2)
        section.right_margin  = Inches(1.2)

    _add_title(doc, title)
    doc.add_paragraph()  # spacing

    for line in llm_text.splitlines():
        line = line.strip()
        if not line:
            doc.add_paragraph()
            continue

        if line.startswith("## "):
            _add_heading(doc, line[3:], level=1)
        elif line.startswith("### "):
            _add_heading(doc, line[4:], level=2)
        elif re.match(r"^Art(?:icle)?\.?\s+\d+", line, re.IGNORECASE):
            m = re.match(r"^Art(?:icle)?\.?\s+(\d+)\s*[:\-–]?\s*(.*)", line, re.IGNORECASE)
            if m:
                _add_article(doc, m.group(1), m.group(2))
            else:
                _add_body(doc, line)
        elif line.startswith("- ") or line.startswith("• "):
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(line[2:])
            _set_font(run, 11)
        else:
            _add_body(doc, line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ── LLM helpers ────────────────────────────────────────────────────────────

def _llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
        temperature=0.2,
        max_tokens=4096,
    )


# ── Public API ─────────────────────────────────────────────────────────────

def generate_contract_docx(description: str) -> tuple[str, bytes]:
    """
    Génère un contrat complet conforme au droit mauritanien.
    Retourne (titre, docx_bytes).
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    system = (
        "Tu es un expert juridique spécialisé en droit mauritanien (Code du Travail Loi N° 2004-017, "
        "Code des Obligations et des Contrats, Convention Collective Générale du Travail). "
        "Génère un contrat complet, structuré et conforme à la législation mauritanienne en vigueur. "
        "Structure le document avec des sections claires marquées ## pour les titres principaux "
        "et ### pour les sous-titres. Numérote chaque clause sous la forme 'Article N — texte'. "
        "Inclus toutes les mentions légales obligatoires. Réponds uniquement avec le texte du contrat, "
        "sans introduction ni commentaire."
    )
    prompt = f"Génère le contrat suivant : {description}"

    resp = _llm().invoke([SystemMessage(content=system), HumanMessage(content=prompt)])
    content = resp.content

    # Extract a title from the first non-empty line or use description
    first_line = next((l.strip().lstrip("#").strip() for l in content.splitlines() if l.strip()), description)
    title = first_line if len(first_line) < 80 else description[:80]

    return title, _build_docx(title, content)


def correct_contract_docx(analysis_rec: dict) -> tuple[str, bytes]:
    """
    Génère une version corrigée du contrat en appliquant les recommandations des findings.
    Retourne (titre, docx_bytes).
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    findings = analysis_rec.get("findings", [])
    extracted = analysis_rec.get("extracted", {})

    findings_text = "\n".join(
        f"- Clause {f.get('clause_id')} | {f.get('verdict')} | "
        f"Art. {f.get('cited_article_id')} | Recommandation: {f.get('recommendation', '')}"
        for f in findings
    )

    system = (
        "Tu es un expert juridique spécialisé en droit mauritanien. "
        "Corrige le contrat en appliquant toutes les recommandations listées. "
        "Génère le contrat corrigé complet, structuré avec ## pour les titres et "
        "'Article N — texte' pour les clauses. "
        "Ne fournis que le texte du contrat corrigé, sans explication."
    )
    prompt = (
        f"Données extraites du contrat original :\n{extracted}\n\n"
        f"Problèmes détectés (à corriger) :\n{findings_text}\n\n"
        "Génère la version corrigée et conforme au droit mauritanien."
    )

    resp = _llm().invoke([SystemMessage(content=system), HumanMessage(content=prompt)])
    content = resp.content

    first_line = next((l.strip().lstrip("#").strip() for l in content.splitlines() if l.strip()), "Contrat corrigé")
    title = f"Contrat corrigé — {first_line[:60]}"

    return title, _build_docx(title, content)
