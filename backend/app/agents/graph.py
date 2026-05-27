"""LangGraph wiring: extraction → matching → verification → reporting.

Linear graph for the MVP. Future iterations can branch (e.g. Self-RAG style
correction loops, parallel per-clause verification, etc.).
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agents.extraction import extraction_node
from app.agents.matching import matching_node
from app.agents.reporting import reporting_node
from app.agents.state import ConformityState
from app.agents.verification import verification_node


@lru_cache(maxsize=1)
def build_graph():
    g = StateGraph(ConformityState)
    g.add_node("extract", extraction_node)
    g.add_node("match", matching_node)
    g.add_node("verify", verification_node)
    g.add_node("reporter", reporting_node)

    g.add_edge(START, "extract")
    g.add_edge("extract", "match")
    g.add_edge("match", "verify")
    g.add_edge("verify", "reporter")
    g.add_edge("reporter", END)

    return g.compile()


def run_verification(contract_text: str, contract_type: str = "statuts", contract_id: str = "") -> ConformityState:
    graph = build_graph()
    initial: ConformityState = {
        "contract_text": contract_text,
        "contract_type": contract_type,
        "contract_id": contract_id,
    }
    return graph.invoke(initial)
