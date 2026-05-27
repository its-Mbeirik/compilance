"""
Endpoints REST — implémentés au Jalon 4.
POST  /api/analyses           → soumet un contrat, retourne analysis_id
GET   /api/analyses/{id}      → statut + findings
GET   /api/analyses/{id}/report → téléchargement PDF
POST  /api/chat/{id}          → Q&A optionnelle
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/analyses")
async def list_analyses():
    return {"message": "Jalon 4 — non implémenté"}
