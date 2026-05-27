# Système Agentique de Vérification de Conformité Contractuelle

Multi-agent system that verifies Mauritanian contracts (company statutes,
employment contracts) against the applicable law using **LangGraph + RAG +
PostgreSQL/pgvector**. PFE — Licence Professionnelle DI/IG/RT, ISCAE Mauritanie.

## Architecture

```
┌────────────┐    ┌─────────────────────────────────────────────┐
│ Next.js 15 │ ─► │ FastAPI                                     │
│ frontend   │    │  └─ LangGraph: extract → match → verify     │
└────────────┘    │                                  └─► report │
                  │  └─ pgvector retriever (bge-m3 embeddings) │
                  └─────────────┬───────────────────────────────┘
                                ▼
                  ┌─────────────────────────────┐
                  │ PostgreSQL 17 + pgvector    │
                  │  - legal_chunks (corpus)    │
                  │  - contracts                │
                  │  - findings                 │
                  └─────────────────────────────┘
```

| Layer | Choice |
|---|---|
| LLM | DeepSeek (OpenAI-compatible API) |
| Embeddings | `BAAI/bge-m3` — local, multilingual (FR/AR), 1024-dim |
| Vector DB | PostgreSQL 17 + pgvector (HNSW index, cosine) |
| Agent framework | LangGraph + LangChain |
| Backend | FastAPI + SQLAlchemy 2 (Python 3.11) |
| Frontend | Next.js 15 + Tailwind 3 + React 19 |
| Doc parsing | pypdf, python-docx |

## Project layout

```
.
├── backend/
│   ├── app/
│   │   ├── agents/       # extraction, matching, verification, reporting + LangGraph
│   │   ├── api/          # FastAPI routers: /contracts, /corpus
│   │   ├── db/           # SQLAlchemy models + session (pgvector)
│   │   ├── llm/          # DeepSeek client
│   │   ├── rag/          # embeddings, chunker, ingestion, retriever
│   │   ├── utils/        # PDF/DOCX/MD loaders
│   │   ├── config.py     # pydantic-settings, reads .env
│   │   └── main.py       # FastAPI entrypoint
│   ├── scripts/
│   │   └── ingest_corpus.py
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js App Router: /, /upload, /reports/[id]
│   ├── components/
│   ├── lib/api.ts
│   └── package.json
├── infra/
│   └── postgres/init.sql # enables pgvector
├── ressourse/ressourse/  # legal corpus (PDFs)
├── tests/
│   ├── test1_statuts/    # SARL statutes + ground truth
│   └── test2_emploi/     # (TBD)
├── docker-compose.yml    # postgres + pgvector
├── .env / .env.example
└── README.md
```

## Quick start (Windows / PowerShell)

### 1. Start Postgres + pgvector

```powershell
docker compose up -d
```

Wait ~5s for the healthcheck. Verify:
```powershell
docker compose ps
```

### 2. Install backend deps

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> First run downloads the `BAAI/bge-m3` model (~2GB) into `data/embeddings_cache/`.

### 3. Ingest the legal corpus

```powershell
python -m scripts.ingest_corpus
```

This walks `ressourse/ressourse/`, chunks each PDF by article, embeds with bge-m3,
and writes to `legal_chunks`. Expect 5–10 min the first time (model download + ingestion).

### 4. Run the API

```powershell
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Health:     http://localhost:8000/health
- Corpus stats: http://localhost:8000/corpus/stats
- Search test:  http://localhost:8000/corpus/search?q=capital+social+SARL&k=5

### 5. Run the frontend

```powershell
cd ..\frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Verifying Test #1 (SARL statutes)

1. Convert the test markdown to PDF (optional) :
   ```powershell
   # if you have pandoc installed
   pandoc tests/test1_statuts/statuts_technova_sarl.md -o tests/test1_statuts/statuts_technova_sarl.pdf
   ```
   Or upload the `.md` directly — the loader handles it.
2. Go to http://localhost:3000/upload, select **Statuts d'entreprise**, upload the file.
3. The report page polls every 3s until completion.
4. Compare detected findings with `tests/test1_statuts/expected_findings.md`
   to compute precision / recall (Phase 5 of the brief).

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health` | Liveness + active models |
| POST | `/contracts/verify` | Upload + queue verification (multipart) |
| GET  | `/contracts/{id}` | Get findings + report (poll until `status=completed`) |
| GET  | `/contracts/` | List all submitted contracts |
| GET  | `/corpus/stats` | Chunks per source file |
| GET  | `/corpus/search?q=...&k=5` | Vector search debug endpoint |

## Roadmap

- [x] Phase 1 — Corpus collected
- [x] Phase 2 — pgvector + LangGraph multi-agents
- [x] Phase 3 — Extraction / matching / verification / reporting agents
- [x] Phase 4 — Web app (FastAPI + Next.js)
- [ ] Phase 5 — Benchmark Test #1 (statuts) + Test #2 (contrat travail)
- [ ] Self-RAG / Corrective-RAG loop for ambiguous findings
- [ ] Interactive Q&A mode on a specific clause
- [ ] Docker image for backend + production docker-compose

## Troubleshooting

- **`psycopg.OperationalError: connection refused`** → Postgres container not up. Run `docker compose up -d` and wait for the healthcheck.
- **bge-m3 model download fails** → Set `HF_HUB_OFFLINE=0`, check network. Manually:
  `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"`.
- **`vector type does not exist`** → pgvector extension missing. Re-create the volume:
  `docker compose down -v && docker compose up -d`.
- **CORS errors in frontend** → Check `FRONTEND_PORT` in `.env` matches `npm run dev` port.
