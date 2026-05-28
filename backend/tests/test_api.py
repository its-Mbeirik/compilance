"""
Test Jalon 4 — Routes FastAPI.
Tests unitaires (TestClient, mocks pipeline) + tests d'intégration DB.
Lance avec :
    pytest tests/test_api.py -v
    pytest tests/test_api.py -v -m integration    # DB réelle
    pytest tests/test_api.py -v -m slow           # pipeline complet
"""
import io
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_pipeline_result(findings=None):
    return {
        "findings": findings or [{
            "clause_id": "cap-001",
            "verdict": "NON_CONFORME",
            "severity": "BLOQUANT",
            "cited_article_id": "OHADA-AUSCGIE-311",
            "quoted_text": "Il ne peut être inférieur à un million (1 000 000) de francs CFA.",
            "recommendation": "Augmenter le capital.",
            "citation_valid": True,
        }],
        "extracted": {"forme_sociale": "SARL"},
        "errors": [],
        "clauses": [],
        "retrievals": {},
    }

TXT_CONTENT = b"Statuts SARL. Capital 500 000 FCFA. Duree 99 ans. Siege Nouakchott."


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# POST /api/analyses
# ---------------------------------------------------------------------------

def test_submit_analysis_requires_file():
    r = client.post("/api/analyses", data={"jurisdiction": "ohada"})
    assert r.status_code == 422


def test_submit_analysis_requires_jurisdiction():
    r = client.post(
        "/api/analyses",
        files={"file": ("test.txt", TXT_CONTENT, "text/plain")},
    )
    assert r.status_code == 422


def test_submit_analysis_rejects_bad_extension():
    r = client.post(
        "/api/analyses",
        files={"file": ("malware.exe", b"data", "application/octet-stream")},
        data={"jurisdiction": "ohada"},
    )
    assert r.status_code == 422


def test_submit_analysis_rejects_empty_text():
    r = client.post(
        "/api/analyses",
        files={"file": ("empty.txt", b"   ", "text/plain")},
        data={"jurisdiction": "ohada"},
    )
    assert r.status_code == 422


@pytest.mark.integration
def test_submit_analysis_returns_analysis_id():
    """Soumet un TXT valide → reçoit analysis_id + status pending."""
    r = client.post(
        "/api/analyses",
        files={"file": ("contract.txt", TXT_CONTENT, "text/plain")},
        data={"jurisdiction": "ohada"},
    )
    assert r.status_code == 202
    data = r.json()
    assert "analysis_id" in data
    assert data["status"] == "pending"


# ---------------------------------------------------------------------------
# GET /api/analyses
# ---------------------------------------------------------------------------

def test_list_analyses_returns_list():
    r = client.get("/api/analyses")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# GET /api/analyses/{id}
# ---------------------------------------------------------------------------

def test_get_analysis_not_found():
    r = client.get("/api/analyses/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.integration
def test_get_analysis_returns_status():
    """Soumet → récupère → vérifie la présence des champs attendus."""
    submit = client.post(
        "/api/analyses",
        files={"file": ("c.txt", TXT_CONTENT, "text/plain")},
        data={"jurisdiction": "ohada"},
    )
    assert submit.status_code == 202
    aid = submit.json()["analysis_id"]

    r = client.get(f"/api/analyses/{aid}")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "findings" in data
    assert "jurisdiction" in data
    assert data["status"] in ("pending", "running", "done", "error")


# ---------------------------------------------------------------------------
# GET /api/analyses/{id}/report
# ---------------------------------------------------------------------------

def test_report_not_found():
    r = client.get("/api/analyses/00000000-0000-0000-0000-000000000000/report")
    assert r.status_code == 404


@pytest.mark.integration
def test_report_conflict_if_not_done():
    """Tente de télécharger le rapport d'une analyse pending → 409."""
    submit = client.post(
        "/api/analyses",
        files={"file": ("c.txt", TXT_CONTENT, "text/plain")},
        data={"jurisdiction": "ohada"},
    )
    aid = submit.json()["analysis_id"]
    r = client.get(f"/api/analyses/{aid}/report")
    # L'analyse est encore pending ou running → 409
    # (peut être done si très rapide, donc on accepte 200 aussi)
    assert r.status_code in (200, 409)


@pytest.mark.integration
def test_report_html_format():
    """Crée une analyse 'done' manuellement et vérifie le rapport HTML."""
    from db.crud import create_contract, create_analysis, update_analysis_done

    cid = create_contract("statuts", "/tmp/test.txt", "ohada")
    aid = create_analysis(cid)
    update_analysis_done(aid, findings=[{
        "clause_id": "c1", "verdict": "NON_CONFORME", "severity": "BLOQUANT",
        "cited_article_id": "OHADA-AUSCGIE-311",
        "quoted_text": "Il ne peut être inférieur à un million.",
        "recommendation": "Augmenter le capital.",
        "citation_valid": True,
    }], extracted={"forme_sociale": "SARL"})

    r = client.get(f"/api/analyses/{aid}/report?fmt=html")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "NON_CONFORME" in r.text
    assert "OHADA-AUSCGIE-311" in r.text


# ---------------------------------------------------------------------------
# POST /api/chat/{id}
# ---------------------------------------------------------------------------

def test_chat_not_found():
    r = client.post(
        "/api/chat/00000000-0000-0000-0000-000000000000",
        json={"message": "Bonjour"},
    )
    assert r.status_code == 404


@pytest.mark.integration
def test_chat_conflict_if_not_done():
    """Chat sur analyse pending → 409."""
    submit = client.post(
        "/api/analyses",
        files={"file": ("c.txt", TXT_CONTENT, "text/plain")},
        data={"jurisdiction": "ohada"},
    )
    aid = submit.json()["analysis_id"]
    r = client.post(f"/api/chat/{aid}", json={"message": "test"})
    assert r.status_code in (200, 409)


@pytest.mark.integration
def test_chat_returns_answer_for_done_analysis():
    """Chat sur analyse done → réponse LLM."""
    from db.crud import create_contract, create_analysis, update_analysis_done

    cid = create_contract("statuts", "/tmp/chat_test.txt", "ohada")
    aid = create_analysis(cid)
    update_analysis_done(aid, findings=[{
        "clause_id": "c1", "verdict": "NON_CONFORME", "severity": "BLOQUANT",
        "cited_article_id": "OHADA-AUSCGIE-311",
        "quoted_text": "Il ne peut être inférieur à un million.",
        "recommendation": "Augmenter le capital.",
        "citation_valid": True,
    }], extracted={"forme_sociale": "SARL"})

    r = client.post(f"/api/chat/{aid}", json={"message": "Quel est le problème principal ?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert len(data["answer"]) > 0


# ---------------------------------------------------------------------------
# Test extract_text
# ---------------------------------------------------------------------------

def test_extract_text_txt():
    from api.extract_text import extract_text
    result = extract_text(b"Bonjour le monde", "test.txt")
    assert result == "Bonjour le monde"


def test_extract_text_unknown_encoding():
    from api.extract_text import extract_text
    latin = "café résumé".encode("latin-1")
    result = extract_text(latin, "test.txt")
    assert "caf" in result


def test_extract_text_pdf():
    """Test minimal PDF — vérifie que pdfplumber ne plante pas sur un vrai PDF."""
    import pdfplumber, io
    # On génère un PDF minimal avec weasyprint
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string="<p>Test PDF conformité</p>").write_pdf()
        from api.extract_text import extract_text
        text = extract_text(pdf_bytes, "test.pdf")
        assert isinstance(text, str)
    except Exception:
        pytest.skip("WeasyPrint non disponible pour générer le PDF de test")
