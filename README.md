# ConformIA — Assistant de Conformité Contractuelle

Assistant juridique intelligent spécialisé en **droit mauritanien** : analyse de contrats, Q&A juridique, génération et correction de documents Word.

---

## Fonctionnalités

- **Analyse de conformité** — soumettez un contrat (PDF, DOCX, TXT) pour obtenir une analyse clause par clause avec verdict, sévérité et recommandations
- **Q&A juridique** — posez des questions libres sur le droit du travail mauritanien, le COC ou la Convention Collective, sans avoir à joindre de document
- **Génération de contrats** — décrivez le contrat souhaité, l'assistant génère un document Word conforme à la législation mauritanienne
- **Correction de contrats** — après une analyse, demandez la version corrigée : l'assistant applique toutes les recommandations et produit un `.docx`
- **Historique** — sidebar avec toutes les analyses passées, rechargement en un clic

---

## Corpus juridique (2 176 articles embeddings BGE-M3)

| Source | Articles |
|--------|----------|
| Code du Travail — Loi N° 2004-017 | 450 |
| Code du Commerce — Loi N° 2000-05 + amendements 2021 | 424 |
| Code des Obligations et des Contrats — Ordonnance N° 89-126 | 1 181 |
| Convention Collective Générale du Travail (UNICEMA/UTM) | 71 |
| Conventions Internationales du Travail ratifiées par la Mauritanie (OIT) | 50 |
| **Total** | **2 176** |

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Frontend | Next.js 15 (App Router, standalone output) |
| Backend | FastAPI + LangGraph |
| LLM | DeepSeek Chat (API compatible OpenAI) |
| Embeddings | BAAI/bge-m3 (1024 dim, multilingue fr/ar) |
| Base de données | PostgreSQL 16 + pgvector |
| Cache | Redis 7 |
| Génération documents | python-docx |
| Containerisation | Docker Compose |

---

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et en cours d'exécution
- Une clé API DeepSeek ([platform.deepseek.com](https://platform.deepseek.com))

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/its-Mbeirik/compilance.git
cd compilance
```

### 2. Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
POSTGRES_USER=conformite
POSTGRES_PASSWORD=conformite_secret
POSTGRES_DB=conformite_db

DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_BASE=https://api.deepseek.com
LLM_MODEL=deepseek-chat

EMBEDDING_MODEL=BAAI/bge-m3
```

### 3. Lancer l'application

```bash
docker compose up --build
```

Au premier démarrage, le backend ingère automatiquement les 2 176 articles juridiques avec leurs embeddings BGE-M3 (environ 40 minutes sur CPU).

### 4. Accéder à l'application

| Service | URL |
|---------|-----|
| Application web | http://localhost:3000 |
| API backend | http://localhost:8000 |
| Documentation API | http://localhost:8000/docs |

---

## Utilisation

### Analyse de contrat
1. Cliquez sur l'icône trombone dans le chat
2. Sélectionnez un fichier PDF, DOCX ou TXT
3. Appuyez sur Entrée — l'analyse se lance automatiquement
4. Consultez les résultats et téléchargez le rapport PDF

### Q&A juridique
Posez directement votre question dans le chat sans joindre de fichier :
> *"Quelle est la durée légale du travail en Mauritanie ?"*
> *"Quelles sont les conditions d'un licenciement pour faute grave ?"*

### Génération de contrat
Tapez une commande directe (commençant par "génère" ou "rédige") :
> *"Génère un contrat CDD 6 mois pour un technicien informatique"*
> *"Rédige un contrat CDI pour un directeur commercial"*

### Correction de contrat
Après avoir analysé un contrat, tapez :
> *"Corrige ce contrat selon les recommandations"*

---

## Architecture

```
assistant_conformite/
├── backend/
│   ├── agents/          # Nœuds LangGraph (extractor, retriever, verifier)
│   ├── api/             # Routes FastAPI + génération de documents
│   ├── db/              # PostgreSQL / pgvector CRUD
│   ├── graph/           # Pipeline LangGraph
│   ├── ingestion/       # Embeddings BGE-M3 + seed articles
│   └── Dockerfile
├── frontend/
│   ├── app/             # Next.js App Router (page unique)
│   └── Dockerfile
├── resourse/            # PDFs des textes juridiques mauritaniens
├── docker-compose.yml
└── .env                 # Non versionné — à créer manuellement
```

---

## Développement

### Relancer uniquement le frontend après modification

```bash
docker compose build frontend && docker compose up -d frontend
```

### Re-seeder la base de données

```bash
docker compose exec backend python -m ingestion.ingest --seed
```

### Lancer les tests

```bash
docker compose exec backend pytest
```

---

## Licence

Projet académique — ISCAE, Semestre 6, PFE 2026.
