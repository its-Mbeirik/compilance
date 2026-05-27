.PHONY: up down logs test test-unit test-db test-embeddings lint setup-env

# --- Infrastructure ---
up:
	docker compose up -d

down:
	docker compose down -v

logs:
	docker compose logs -f backend

ps:
	docker compose ps

# --- Setup ---
setup-env:
	cp .env.example .env
	@echo "Edite .env et ajoute tes cles API"

install-backend:
	cd backend && pip install -r requirements.txt

# --- Tests Jalon 1 ---
test-unit:
	cd backend && python -m pytest tests/test_schemas.py tests/test_guards.py -v

test-db:
	cd backend && python -m pytest tests/test_db.py -v -m integration

test-embeddings:
	cd backend && python -m pytest tests/test_embeddings.py -v -m slow

# Lance tous les tests du Jalon 1
test-jalon1: test-unit test-db test-embeddings
	@echo "=== Jalon 1 : tous les tests passes ==="

# --- Lint ---
lint:
	cd backend && python -m ruff check . && python -m mypy shared/ --ignore-missing-imports

# --- Validation manuelle ---
validate-pgvector:
	docker compose exec postgres psql -U conformite -d conformite_db -c "SELECT extname FROM pg_extension WHERE extname='vector';"

validate-tables:
	docker compose exec postgres psql -U conformite -d conformite_db -c "\dt"
