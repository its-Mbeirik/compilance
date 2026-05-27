"""Reporting agent.

Aggregates all findings into a human-readable Markdown report with executive
summary, severity counts, per-clause details, and a recommendations section.
"""

from __future__ import annotations

import logging
from collections import Counter

from app.agents.state import ConformityState

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"CRITIQUE": 0, "MAJEURE": 1, "MINEURE": 2}
SEVERITY_LABEL = {"CRITIQUE": "[CRITIQUE]", "MAJEURE": "[MAJEURE]", "MINEURE": "[MINEURE]"}


def reporting_node(state: ConformityState) -> ConformityState:
    findings = sorted(
        state.get("findings", []),
        key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.clause_ref or ""),
    )
    contract_type = state.get("contract_type", "contrat")
    clauses = state.get("clauses", [])
    counts = Counter(f.severity for f in findings)

    lines = []
    lines.append(f"# Rapport de Conformité — {contract_type.title()}")
    lines.append("")
    lines.append("## Synthèse exécutive")
    lines.append("")
    lines.append(f"- Clauses analysées : **{len(clauses)}**")
    lines.append(f"- Non-conformités détectées : **{len(findings)}**")
    lines.append(f"  - Critiques : {counts.get('CRITIQUE', 0)}")
    lines.append(f"  - Majeures : {counts.get('MAJEURE', 0)}")
    lines.append(f"  - Mineures : {counts.get('MINEURE', 0)}")
    lines.append("")

    if not findings:
        lines.append("**Aucune non-conformité détectée.** Le document semble conforme aux dispositions légales examinées.")
        return {"report": "\n".join(lines)}

    lines.append("## Détail des non-conformités")
    lines.append("")
    for i, f in enumerate(findings, 1):
        label = SEVERITY_LABEL.get(f.severity, f.severity)
        ref = f.clause_ref or "(clause manquante)"
        lines.append(f"### {i}. {label} {ref}")
        lines.append(f"**Catégorie :** {f.category}")
        lines.append("")
        lines.append(f"**Problème :** {f.description}")
        lines.append("")
        if f.recommendation:
            lines.append(f"**Recommandation :** {f.recommendation}")
            lines.append("")
        if f.legal_basis:
            lines.append("**Base légale :**")
            for lc in f.legal_basis:
                art = f" — {lc.article}" if lc.article else ""
                lines.append(f"- *{lc.source}{art}* : « {lc.excerpt[:300]}{'...' if len(lc.excerpt) > 300 else ''} »")
            lines.append("")
        lines.append(f"*Confiance : {f.confidence:.0%}*")
        lines.append("")
        lines.append("---")
        lines.append("")

    return {"report": "\n".join(lines)}
