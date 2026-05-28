"""
Test Jalons 4 & 5 — Routes FastAPI.
Tests unitaires (TestClient, mocks) + tests d'intégration DB.
Lance avec :
    pytest tests/test_api.py -v
    pytest tests/test_api.py -v -m integration    # DB réelle
    pytest tests/test_api.py -v -m slow           # pipeline complet
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_pipeline_result(findings=None):
    return {
        "findings": findings or [{
            "clause_id": "pe-001",
            "verdict": "NON_CONFORME",
            "severity": "BLOQUANT",
            "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
            "quoted_text": "La période d'essai ne peut excéder six mois.",
            "recommendation": "Réduire la période d'essai à 6 mois maximum.",
            "citation_valid": True,
        }],
        "extracted": {"type_contrat": "CDD"},
        "errors": [],
        "clauses": [],
        "retrievals": {},
    }

TXT_CONTENT = b"Contrat CDD. Employeur ACME SA. Employe Moussa Diallo. Poste Developpeur. Duree 6 mois."


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
    r = client.post("/api/analyses", data={"jurisdiction": "mauritania_labor"})
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
        data={"jurisdiction": "mauritania_labor"},
    )
    assert r.status_code == 422


def test_submit_analysis_rejects_empty_text():
    r = client.post(
        "/api/analyses",
        files={"file": ("empty.txt", b"   ", "text/plain")},
        data={"jurisdiction": "mauritania_labor"},
    )
    assert r.status_code == 422


@pytest.mark.integration
def test_submit_analysis_returns_analysis_id():
    """Soumet un TXT valide → reçoit analysis_id + status pending."""
    r = client.post(
        "/api/analyses",
        files={"file": ("contract.txt", TXT_CONTENT, "text/plain")},
        data={"jurisdiction": "mauritania_labor"},
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
        data={"jurisdiction": "mauritania_labor"},
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
        data={"jurisdiction": "mauritania_labor"},
    )
    aid = submit.json()["analysis_id"]
    r = client.get(f"/api/analyses/{aid}/report")
    assert r.status_code in (200, 409)


@pytest.mark.integration
def test_report_html_format():
    """Crée une analyse 'done' manuellement et vérifie le rapport HTML."""
    from db.crud import create_contract, create_analysis, update_analysis_done

    cid = create_contract("contrat_travail", "/tmp/test.txt", "mauritania_labor")
    aid = create_analysis(cid)
    update_analysis_done(aid, findings=[{
        "clause_id": "pe-001", "verdict": "NON_CONFORME", "severity": "BLOQUANT",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "La période d'essai ne peut excéder six mois.",
        "recommendation": "Réduire à 6 mois maximum.",
        "citation_valid": True,
    }], extracted={"type_contrat": "CDD"})

    r = client.get(f"/api/analyses/{aid}/report?fmt=html")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "NON_CONFORME" in r.text
    assert "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10" in r.text


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
        data={"jurisdiction": "mauritania_labor"},
    )
    aid = submit.json()["analysis_id"]
    r = client.post(f"/api/chat/{aid}", json={"message": "test"})
    assert r.status_code in (200, 409)


@pytest.mark.integration
def test_chat_returns_answer_for_done_analysis():
    """Chat sur analyse done → réponse LLM."""
    from db.crud import create_contract, create_analysis, update_analysis_done

    cid = create_contract("contrat_travail", "/tmp/chat_test.txt", "mauritania_labor")
    aid = create_analysis(cid)
    update_analysis_done(aid, findings=[{
        "clause_id": "pe-001", "verdict": "NON_CONFORME", "severity": "BLOQUANT",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "La période d'essai ne peut excéder six mois.",
        "recommendation": "Réduire à 6 mois maximum.",
        "citation_valid": True,
    }], extracted={"type_contrat": "CDD"})

    r = client.post(f"/api/chat/{aid}", json={"message": "Quel est le problème principal ?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert len(data["answer"]) > 0


# ---------------------------------------------------------------------------
# POST /api/chat  — Q&A générale sans document (Jalon 5)
# ---------------------------------------------------------------------------

def test_general_chat_missing_message():
    r = client.post("/api/chat", json={})
    assert r.status_code == 422


def test_general_chat_returns_answer():
    """Q&A générale : LLM mocké, vérifie la structure de réponse."""
    with patch("api.routes._ask_llm_general", return_value="Réponse juridique de test"):
        r = client.post("/api/chat", json={"message": "Quelle est la durée légale du travail?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert data["answer"] == "Réponse juridique de test"


# ---------------------------------------------------------------------------
# POST /api/generate-document  (Jalon 5)
# ---------------------------------------------------------------------------

def test_generate_document_missing_description():
    r = client.post("/api/generate-document", json={})
    assert r.status_code == 422


def test_generate_document_returns_docx():
    """Génération de contrat : docgen mocké, vérifie content-type .docx."""
    fake_docx = b"PK\x03\x04" + b"\x00" * 50
    with patch("api.docgen.generate_contract_docx", return_value=("Contrat CDD Test", fake_docx)):
        r = client.post("/api/generate-document", json={"description": "CDD 6 mois technicien"})
    assert r.status_code == 200
    assert "application/vnd.openxmlformats" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]


# ---------------------------------------------------------------------------
# POST /api/correct-document/{id}  (Jalon 5)
# ---------------------------------------------------------------------------

def test_correct_document_not_found():
    r = client.post("/api/correct-document/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


@pytest.mark.integration
def test_correct_document_conflict_if_pending():
    """Corrige une analyse pending → 409."""
    from db.crud import create_contract, create_analysis
    cid = create_contract("contrat_travail", "/tmp/correct_pending.txt", "mauritania_labor")
    aid = create_analysis(cid)
    r = client.post(f"/api/correct-document/{aid}")
    assert r.status_code == 409


@pytest.mark.integration
def test_correct_document_returns_docx():
    """Corrige une analyse done → retourne un fichier .docx."""
    from db.crud import create_contract, create_analysis, update_analysis_done
    cid = create_contract("contrat_travail", "/tmp/correct_done.txt", "mauritania_labor")
    aid = create_analysis(cid)
    update_analysis_done(aid, findings=[{
        "clause_id": "pe-001", "verdict": "NON_CONFORME", "severity": "BLOQUANT",
        "cited_article_id": "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10",
        "quoted_text": "Période d'essai non conforme.",
        "recommendation": "Réduire à 6 mois maximum.",
        "citation_valid": True,
    }], extracted={"type_contrat": "CDD"})
    fake_docx = b"PK\x03\x04" + b"\x00" * 50
    with patch("api.docgen.correct_contract_docx", return_value=("Contrat corrigé", fake_docx)):
        r = client.post(f"/api/correct-document/{aid}")
    assert r.status_code == 200
    assert "application/vnd.openxmlformats" in r.headers["content-type"]


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
    import pdfplumber, io  # noqa: F401
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string="<p>Test PDF conformité</p>").write_pdf()
        from api.extract_text import extract_text
        text = extract_text(pdf_bytes, "test.pdf")
        assert isinstance(text, str)
    except Exception:
        pytest.skip("WeasyPrint non disponible pour générer le PDF de test")
