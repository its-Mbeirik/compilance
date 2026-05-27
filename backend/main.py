import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Assistant de Conformité Contractuelle",
    description="Système agentique de vérification OHADA / Code du Travail Mauritanien",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


from api.routes import router
app.include_router(router, prefix="/api")
