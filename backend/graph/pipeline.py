"""
Jalon 3 — Pipeline LangGraph.
Câble les trois nœuds : Extracteur → Récupérateur → Vérificateur.
Supporte MemorySaver (dev/test) et PostgresSaver (production).
"""
import logging
import uuid
from typing import Any, Optional

from langgraph.graph import END, START, StateGraph

from agents.extractor import extractor_node
from agents.retriever import retriever_node
from agents.verifier import verifier_node
from shared.schemas import AgentState

logger = logging.getLogger(__name__)


def _build_graph() -> StateGraph:
    g = StateGraph(AgentState)
    g.add_node("extractor", extractor_node)
    g.add_node("retriever", retriever_node)
    g.add_node("verifier", verifier_node)
    g.add_edge(START, "extractor")
    g.add_edge("extractor", "retriever")
    g.add_edge("retriever", "verifier")
    g.add_edge("verifier", END)
    return g


def build_pipeline(use_postgres: bool = False):
    """
    Compile et retourne le pipeline LangGraph.

    Args:
        use_postgres: Si True, utilise PostgresSaver pour la persistance des checkpoints.
                      Nécessite DATABASE_URL dans l'environnement.
                      Sinon, utilise MemorySaver (dev/test).
    """
    from langgraph.checkpoint.memory import MemorySaver

    graph = _build_graph()

    if use_postgres:
        try:
            import os
            from langgraph.checkpoint.postgres import PostgresSaver
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL non défini")
            checkpointer = PostgresSaver.from_conn_string(db_url)
            logger.info("Pipeline compilé avec PostgresSaver.")
            return graph.compile(checkpointer=checkpointer)
        except Exception as exc:
            logger.warning(
                f"PostgresSaver non disponible ({exc}), fallback MemorySaver."
            )

    checkpointer = MemorySaver()
    logger.info("Pipeline compilé avec MemorySaver.")
    return graph.compile(checkpointer=checkpointer)


def run_pipeline(
    contract_text: str,
    jurisdiction: str,
    contract_id: Optional[str] = None,
    use_postgres: bool = False,
) -> dict[str, Any]:
    """
    Lance le pipeline de conformité sur un contrat.

    Args:
        contract_text: Texte brut du contrat.
        jurisdiction:  'ohada' ou 'mauritania_labor'.
        contract_id:   Identifiant unique (généré si absent).
        use_postgres:  Activer PostgresSaver pour la persistance.

    Returns:
        L'état final du graphe avec 'findings', 'extracted', 'errors', etc.
    """
    if contract_id is None:
        contract_id = str(uuid.uuid4())

    pipeline = build_pipeline(use_postgres=use_postgres)

    initial_state: AgentState = {
        "contract_id": contract_id,
        "contract_text": contract_text,
        "jurisdiction": jurisdiction,
        "extracted": {},
        "clauses": [],
        "retrievals": {},
        "findings": [],
        "errors": [],
    }

    config = {"configurable": {"thread_id": contract_id}}

    logger.info(
        f"Lancement pipeline — contract_id={contract_id}, jurisdiction={jurisdiction}"
    )
    result = pipeline.invoke(initial_state, config=config)
    logger.info(
        f"Pipeline terminé — {len(result.get('findings', []))} findings, "
        f"{len(result.get('errors', []))} erreurs"
    )
    return result
