import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.land_service import land_service

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["mock_mode"] is True
    assert data["database"]["total_properties"] == 6
    assert data["database"]["clean_properties"] == 5
    assert data["database"]["risk_flagged_properties"] == 1

def test_get_all_lands():
    response = client.get("/api/lands")
    assert response.status_code == 200
    lands = response.json()
    assert len(lands) == 6
    ids = [l["id"] for l in lands]
    assert "bv-hyd-01" in ids
    assert "bv-hyd-04" in ids

def test_filter_lands():
    # Filter by min acres 10.0
    response = client.get("/api/lands?min_acres=10.0")
    assert response.status_code == 200
    lands = response.json()
    assert len(lands) >= 2
    for l in lands:
        assert l["acres"] >= 10.0

def test_disputed_property_details():
    # Plot 4 is bv-hyd-04
    response = client.get("/api/lands/bv-hyd-04")
    assert response.status_code == 200
    land = response.json()
    assert "Disputed" in land["legal_status"]
    assert len(land["legal_risks"]) >= 2
    risk_types = [r["risk_type"] for r in land["legal_risks"]]
    assert any("Mortgage" in rt or "Lien" in rt for rt in risk_types)
    assert any("Inheritance" in rt or "Heir" in rt for rt in risk_types)

def test_compare_lands():
    payload = {"land_ids": ["bv-hyd-01", "bv-hyd-04"]}
    response = client.post("/api/lands/compare", json=payload)
    assert response.status_code == 200
    compared = response.json()
    assert len(compared) == 2

def test_pdf_report_generation():
    response = client.get("/api/lands/bv-hyd-01/report")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 1000 # Valid generated PDF bytes

def test_ai_chat_prompt_1_clean_10_acre():
    payload = {
        "query": "Show me 10-acre clean agricultural land near Hyderabad",
        "language": "en"
    }
    response = client.post("/api/ai/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "bv-hyd-01" in data["matched_land_ids"]
    assert data["ai_mode"] == "MOCK AI"
    assert data["audio_available"] is True
    assert len(data["response"]) > 0

def test_ai_chat_prompt_2_plot_4_safety():
    payload = {
        "query": "Is Plot 4 safe to buy?",
        "language": "en"
    }
    response = client.post("/api/ai/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "bv-hyd-04" in data["matched_land_ids"]
    assert any("mortgage" in w.lower() or "lien" in w.lower() for w in data["legal_warnings"])
    assert "NOT SAFE" in data["response"] or "WARNING" in data["response"] or "warning" in data["response"].lower()

def test_ai_chat_prompt_3_highway_claim():
    payload = {
        "query": "Check whether the upcoming highway claim is verified",
        "language": "en"
    }
    response = client.post("/api/ai/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any("RRR" in f or "Highway" in f or "highway" in f.lower() for f in data["infrastructure_findings"])

def test_broker_claim_checker_metro():
    payload = {
        "statement": "A metro station will be built just 2 km from this land next year.",
        "language": "en"
    }
    response = client.post("/api/claims/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verification_status"] == "UNVERIFIED"
    assert data["confidence_level"] == "High"
    assert "HMRL" in data["available_evidence"]

def test_broker_claim_checker_guarantee():
    payload = {
        "statement": "Land price is guaranteed to double in 18 months, completely risk free.",
        "language": "en"
    }
    response = client.post("/api/claims/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verification_status"] == "CONTRADICTED"

def test_document_analysis_clean():
    clean_sample_text = (
        "GOVERNMENT OF TELANGANA REVENUE DEPARTMENT DHARANI PATTA PASSBOOK.\n"
        "Survey Number: SY-101/MOCK. Extent: 10 Acres.\n"
        "Mortgages Registered: NIL. Court Injunctions: NIL. 22-A List: NOT LISTED.\n"
        "Pattadar: K. Raghava Rao."
    )
    files = {"file": ("test_clean.txt", clean_sample_text.encode("utf-8"), "text/plain")}
    response = client.post("/api/documents/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ["LOW", "MODERATE"]
    assert data["encumbrance_clauses_found"] is False

def test_document_analysis_disputed():
    disputed_text = (
        "AGREEMENT OF SALE. Land SY-104/MOCK admeasuring 6.00 Acres at Keesara.\n"
        "The Vendor discloses that the property was hypothecated with Telangana Grameena Bank "
        "against loan A/c TG-AGRI-8832-MOCK for sum of Rs 85,00,000.\n"
        "Pending OS No. 412/2022 in Sub-Court Medchal by sister disputing succession."
    )
    files = {"file": ("test_disputed.txt", disputed_text.encode("utf-8"), "text/plain")}
    response = client.post("/api/documents/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert data["encumbrance_clauses_found"] is True
    assert len(data["detected_issues"]) >= 2

def test_text_to_speech():
    payload = {"text": "భూమివాణి కి స్వాగతం", "language": "te"}
    response = client.post("/api/ai/speak", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["audio_base64"]) > 50
    assert data["format"] == "audio/wav"

def test_speech_to_text():
    mock_audio = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    files = {"file": ("mock.wav", mock_audio, "audio/wav")}
    response = client.post("/api/ai/transcribe", files=files, data={"language": "en"})
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert len(data["transcript"]) > 0
