"""Shared LangGraph state for the conformity-verification workflow.

A single TypedDict is passed between agent nodes. Each node reads what it needs
and adds its own output keys. The list types are merged across iterations.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, Field


def _merge_lists(left: list, right: list) -> list:
    return (left or []) + (right or [])


class Clause(BaseModel):
    ref: str = Field(description="Article or clause reference, e.g. 'Article 7'")
    title: str = Field(default="", description="Short title of the clause")
    text: str = Field(description="Verbatim clause text from the contract")
    topic: str = Field(default="", description="Topic / theme of the clause")


class LegalCitation(BaseModel):
    source: str
    article: str | None = None
    excerpt: str


class Finding(BaseModel):
    clause_ref: str | None = None
    severity: Literal["CRITIQUE", "MAJEURE", "MINEURE"]
    category: str
    description: str
    recommendation: str
    legal_basis: list[LegalCitation] = Field(default_factory=list)
    confidence: float = 0.0


class ConformityState(TypedDict, total=False):
    contract_text: str
    contract_type: str
    contract_id: str

    clauses: Annotated[list[Clause], _merge_lists]
    retrievals: dict[str, Any]
    findings: Annotated[list[Finding], _merge_lists]
    report: str

    error: str | None
