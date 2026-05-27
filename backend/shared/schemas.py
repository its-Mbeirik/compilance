"""
Schémas Pydantic partagés entre les trois nœuds LangGraph.
Consommés par backend/agents/, backend/api/, et backend/ingestion/.
"""
import operator
import uuid
from enum import Enum
from typing import Annotated, List, Literal, Optional
from typing_extensions import TypedDict

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Jurisdiction(str, Enum):
    OHADA = "ohada"
    MAURITANIA_LABOR = "mauritania_labor"


class ClauseType(str, Enum):
    # Types OHADA / statuts
    CAPITAL_SOCIAL = "capital_social"
    DUREE_SOCIETE = "duree_societe"
    SIEGE_SOCIAL = "siege_social"
    MENTIONS_OBLIGATOIRES = "mentions_obligatoires"
    LIBERATION_CAPITAL = "liberation_capital"
    OBJET_SOCIAL = "objet_social"
    FORME_SOCIALE = "forme_sociale"
    PARTS_SOCIALES = "parts_sociales"
    # Types Code du Travail
    TYPE_CONTRAT = "type_contrat"
    PERIODE_ESSAI = "periode_essai"
    DUREE_CDD = "duree_cdd"
    AGE_MINIMUM = "age_minimum"
    CONGES_PAYES = "conges_payes"
    VISA_INSPECTION = "visa_inspection"
    SALAIRE = "salaire"
    # Générique
    AUTRE = "autre"


class FindingVerdict(str, Enum):
    CONFORME = "CONFORME"
    NON_CONFORME = "NON_CONFORME"
    EXIGE_REVUE = "EXIGE_REVUE"


class FindingSeverity(str, Enum):
    BLOQUANT = "BLOQUANT"   # poids ×4 dans F1 pondéré
    MAJEUR = "MAJEUR"       # poids ×2
    MINEUR = "MINEUR"       # poids ×1


# ---------------------------------------------------------------------------
# Modèles de base
# ---------------------------------------------------------------------------

class Clause(BaseModel):
    clause_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    type_clause: ClauseType
    text: str
    jurisdiction_hint: Optional[Jurisdiction] = None


class Article(BaseModel):
    """Un article juridique tel que stocké dans legal_articles et renvoyé par le Récupérateur."""
    id: str                          # ex. "OHADA-AUSCGIE-311"
    jurisdiction: str
    code_name: str
    article_number: str
    hierarchy_path: Optional[str] = None
    full_text: str
    language: str = "fr"
    score: Optional[float] = None    # score du reranker


class Finding(BaseModel):
    """Verdict émis par le Vérificateur sur une clause."""
    clause_id: str
    verdict: FindingVerdict
    cited_article_id: str
    quoted_text: str
    recommendation: Optional[str] = None
    severity: Optional[FindingSeverity] = None
    citation_valid: bool = False     # positionné par citation_guard()


# ---------------------------------------------------------------------------
# Schémas d'extraction — Nœud Extracteur
# ---------------------------------------------------------------------------

class Associe(BaseModel):
    nom: str
    apport_fcfa: float = Field(ge=0)
    parts_nb: int = Field(ge=0)
    nationalite: Optional[str] = None


class StatutsExtraction(BaseModel):
    """Sortie du Nœud Extracteur pour un statut d'entreprise (OHADA)."""
    forme_sociale: Literal["SARL", "SA", "SAS", "SNC", "GIE"]
    denomination: str
    siege_social: str
    objet_social: str
    duree_annees: int = Field(ge=1, le=99,
        description="Durée de la société — Art. 28 AUSCGIE: maximum 99 ans")
    capital_social_fcfa: float = Field(ge=0)
    parts_sociales_nb: int = Field(ge=0)
    parts_sociales_valeur_fcfa: float = Field(ge=0)
    associes: List[Associe] = Field(default_factory=list)
    governing_law_clause: Optional[str] = None
    clauses: List[Clause] = Field(default_factory=list)

    @field_validator("duree_annees")
    @classmethod
    def duree_max_99(cls, v: int) -> int:
        if v > 99:
            raise ValueError("Art. 28 AUSCGIE: durée maximale 99 ans")
        return v


class ContratsExtraction(BaseModel):
    """Sortie du Nœud Extracteur pour un contrat de travail (Code du Travail Mauritanien)."""
    type_contrat: Literal["CDI", "CDD", "CTT", "Stage", "Autre"]
    employeur: str
    employe: str
    poste: str
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None        # CDD uniquement
    duree_mois: Optional[int] = Field(None, ge=0)
    salaire_mensuel_fcfa: Optional[float] = Field(None, ge=0)
    periode_essai_mois: Optional[int] = Field(None, ge=0,
        description="Art. 10: max 6 mois (tous), 12 mois (cadres)")
    est_cadre: bool = False
    age_employe: Optional[int] = Field(None, ge=0,
        description="Art. 153-154: âge minimum 14 ans")
    visa_inspection: Optional[bool] = None  # Art. 18: CDD > 3 mois
    clauses: List[Clause] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# État partagé LangGraph — consommé par les 3 nœuds
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    contract_id: str
    contract_text: str
    jurisdiction: Literal["ohada", "mauritania_labor"]
    extracted: dict                                         # StatutsExtraction | ContratsExtraction .model_dump()
    clauses: list                                           # list[Clause]
    retrievals: dict                                        # {clause_id: list[Article]}
    findings: Annotated[list, operator.add]                 # list[Finding] — accumulation entre nœuds
    errors: Annotated[list, operator.add]                   # list[str]
