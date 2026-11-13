import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_models_health():
    res = client.get("/api/investigate/models/status")
    assert res.status_code == 200
    data = res.json()
    assert "prisma_stt" in data
    assert "reasoning" in data
    assert "timbre_tts" in data
    assert data["prisma_stt"]["role"] == "STT"
    assert data["reasoning"]["role"] == "REASONING"
    assert data["timbre_tts"]["role"] == "TTS"

def test_collaborative_investigation_keesara():
    payload = {
        "query": "Show me 6-acre land near Hyderabad. The broker says a metro station is coming nearby. Is the property safe?",
        "conversation_language": "en"
    }
    res = client.post("/api/investigate/collaborate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "bv-hyd-04" in data["matched_land_ids"]
    assert len(data["dialogue_sequence"]) == 4
    characters = [d["character"] for d in data["dialogue_sequence"]]
    assert "bhoomi" in characters
    assert "infra" in characters
    assert "nyaya" in characters
    assert "amma" in characters

    # Check that audio was synthesized for each character
    for d in data["dialogue_sequence"]:
        assert d["audio_base64"] is not None
        assert len(d["audio_base64"]) > 50

def test_collaborative_investigation_telugu():
    payload = {
        "query": "హైదరాబాద్ దగ్గర 6 ఎకరాల భూమి చూడాలి. బ్రోకర్ మెట్రో వస్తుందని చెప్పారు, ఇది సురక్షితమేనా?",
        "conversation_language": "te"
    }
    res = client.post("/api/investigate/collaborate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["conversation_language"] == "te"
    bhoomi_speech = next(d for d in data["dialogue_sequence"] if d["character"] == "bhoomi")
    assert "భూమి" in bhoomi_speech["text"] or "నమస్కారం" in bhoomi_speech["text"]

def test_switch_reasoning_provider():
    res = client.post("/api/investigate/provider", json={"provider": "MOCK_DEV_ADAPTER"})
    assert res.status_code == 200
    data = res.json()
    assert data["new_provider"] == "MOCK_DEV_ADAPTER"
