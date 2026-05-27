import os
import pytest

# Les tests d'intégration (DB, embeddings) sont marqués et skippés si les services
# ne sont pas disponibles

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: tests nécessitant PostgreSQL")
    config.addinivalue_line("markers", "slow: tests téléchargeant les modèles BGE (~2GB)")


@pytest.fixture(scope="session")
def db_url():
    return os.getenv(
        "DATABASE_URL",
        "postgresql://conformite:conformite_secret@localhost:5432/conformite_db",
    )
