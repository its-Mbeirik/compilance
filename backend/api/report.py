"""
Jalon 4 — Génération du rapport de conformité.
Jinja2 → HTML → WeasyPrint PDF (fallback HTML si WeasyPrint absent).
"""
import logging
from datetime import datetime
from typing import Any

from jinja2 import Environment, BaseLoader

logger = logging.getLogger(__name__)

_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: Arial, sans-serif; font-size: 12px; color: #1a1a1a; margin: 40px; }
  h1   { color: #1e40af; font-size: 20px; border-bottom: 2px solid #1e40af; padding-bottom: 8px; }
  h2   { color: #374151; font-size: 15px; margin-top: 28px; }
  .meta { color: #6b7280; font-size: 11px; margin-bottom: 20px; }
  .summary { display: flex; gap: 20px; margin: 16px 0; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 12px;
           font-size: 11px; font-weight: bold; }
  .CONFORME     { background:#d1fae5; color:#065f46; }
  .NON_CONFORME { background:#fee2e2; color:#991b1b; }
  .EXIGE_REVUE  { background:#fef3c7; color:#92400e; }
  .BLOQUANT { background:#dc2626; color:#fff; }
  .MAJEUR   { background:#f97316; color:#fff; }
  .MINEUR   { background:#9ca3af; color:#fff; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; }
  th { background: #1e40af; color: #fff; padding: 8px; text-align: left; font-size: 11px; }
  td { padding: 7px 8px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
  tr:nth-child(even) td { background: #f9fafb; }
  .quote { font-style: italic; color: #374151; font-size: 10px;
           border-left: 3px solid #d1d5db; padding-left: 8px; margin-top: 4px; }
  .rec { color: #7c3aed; font-size: 10px; margin-top: 3px; }
  .valid-yes { color: #065f46; }
  .valid-no  { color: #991b1b; }
  @page { size: A4; margin: 20mm; }
</style>
</head>
<body>

<h1>Rapport de Conformité Contractuelle</h1>
<div class="meta">
  <strong>Juridiction :</strong> {{ jurisdiction_label }} &nbsp;|&nbsp;
  <strong>Type :</strong> {{ doc_type }} &nbsp;|&nbsp;
  <strong>Généré le :</strong> {{ generated_at }}
</div>

<h2>Résumé</h2>
<table style="width:auto">
  <tr>
    <td style="padding-right:24px"><strong>Total clauses :</strong> {{ total }}</td>
    <td style="padding-right:24px">
      <span class="badge CONFORME">CONFORME {{ counts.CONFORME }}</span>
    </td>
    <td style="padding-right:24px">
      <span class="badge NON_CONFORME">NON_CONFORME {{ counts.NON_CONFORME }}</span>
    </td>
    <td>
      <span class="badge EXIGE_REVUE">EXIGE_REVUE {{ counts.EXIGE_REVUE }}</span>
    </td>
  </tr>
</table>

{% if bloquants %}
<h2 style="color:#dc2626">⚠ Points bloquants ({{ bloquants|length }})</h2>
<ul>
{% for f in bloquants %}
  <li><strong>{{ f.cited_article_id }}</strong> — {{ f.recommendation or "Voir détail" }}</li>
{% endfor %}
</ul>
{% endif %}

<h2>Détail des vérifications</h2>
<table>
  <thead>
    <tr>
      <th style="width:18%">Clause</th>
      <th style="width:12%">Verdict</th>
      <th style="width:10%">Sévérité</th>
      <th style="width:20%">Article cité</th>
      <th>Citation / Recommandation</th>
      <th style="width:7%">Cit. ✓</th>
    </tr>
  </thead>
  <tbody>
  {% for f in findings %}
    <tr>
      <td>{{ f.clause_id }}</td>
      <td><span class="badge {{ f.verdict }}">{{ f.verdict }}</span></td>
      <td>
        {% if f.severity %}
          <span class="badge {{ f.severity }}">{{ f.severity }}</span>
        {% endif %}
      </td>
      <td>{{ f.cited_article_id }}</td>
      <td>
        {% if f.quoted_text %}
          <div class="quote">"{{ f.quoted_text[:200] }}{% if f.quoted_text|length > 200 %}…{% endif %}"</div>
        {% endif %}
        {% if f.recommendation %}
          <div class="rec">→ {{ f.recommendation }}</div>
        {% endif %}
      </td>
      <td class="{{ 'valid-yes' if f.citation_valid else 'valid-no' }}">
        {{ '✓' if f.citation_valid else '✗' }}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>

<p style="margin-top:40px; font-size:10px; color:#9ca3af;">
  Rapport généré automatiquement par le Système Agentique de Vérification de Conformité.
  Les verdicts doivent être confirmés par un professionnel du droit.
</p>
</body>
</html>"""


def _build_context(analysis: dict) -> dict:
    findings = analysis.get("findings", [])
    counts = {"CONFORME": 0, "NON_CONFORME": 0, "EXIGE_REVUE": 0}
    for f in findings:
        v = f.get("verdict", "EXIGE_REVUE")
        counts[v] = counts.get(v, 0) + 1

    jurisdiction_labels = {
        "ohada": "OHADA — Droit des sociétés commerciales",
        "mauritania_labor": "Code du Travail Mauritanien",
    }
    doc_type_labels = {
        "statuts": "Statuts d'entreprise",
        "contrat_travail": "Contrat de travail",
    }

    return {
        "jurisdiction_label": jurisdiction_labels.get(
            analysis.get("jurisdiction", ""), analysis.get("jurisdiction", "—")
        ),
        "doc_type": doc_type_labels.get(
            analysis.get("doc_type", ""), analysis.get("doc_type", "—")
        ),
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total": len(findings),
        "counts": counts,
        "findings": findings,
        "bloquants": [f for f in findings if f.get("severity") == "BLOQUANT"],
    }


def generate_html(analysis: dict) -> str:
    env = Environment(loader=BaseLoader())
    tmpl = env.from_string(_TEMPLATE)
    return tmpl.render(**_build_context(analysis))


def generate_pdf(analysis: dict) -> bytes:
    """
    Retourne les octets du PDF.
    Lève RuntimeError si WeasyPrint échoue.
    """
    html = generate_html(analysis)
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except Exception as exc:
        raise RuntimeError(f"WeasyPrint: {exc}") from exc
