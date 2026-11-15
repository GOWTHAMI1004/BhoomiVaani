import pytest
import json
import json as json_module
from unittest.mock import AsyncMock
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
    assert data["reasoning"]["model_name"] == "Unselected external reasoning model"
    assert data["reasoning"]["connection_status"] == "NOT_CONFIGURED"
    assert data["mock_mode"] is False
    assert data["available_conversation_languages"] == []

def test_collaborative_investigation_keesara():
    payload = {
        "query": "Show me the 6-acre Keesara parcel. The broker says a metro station is coming nearby. Is the property safe?",
        "conversation_language": "en"
    }
    res = client.post("/api/investigate/collaborate", json=payload)
    assert res.status_code == 503
    assert "no external LLM provider has been selected" in res.json()["detail"]

def test_generic_safety_question_does_not_select_an_arbitrary_parcel():
    response = client.post("/api/investigate/collaborate", json={
        "query": "Is this land safe to buy?",
        "conversation_language": "en",
    })
    assert response.status_code == 503
    assert "no external LLM provider has been selected" in response.json()["detail"]


def test_acreage_and_broad_city_alone_do_not_select_a_synthetic_parcel():
    from app.services.reasoning_service import reasoning_service
    from app.services.land_service import land_service

    selected = reasoning_service._select_land(
        "I am looking for 6 acres near Hyderabad.",
        land_service.get_all(),
        None,
    )
    assert selected is None
    response = client.post("/api/investigate/collaborate", json={
        "query": "I am looking for 6 acres near Hyderabad.",
        "conversation_language": "en",
    })
    assert response.status_code == 503


def test_conversation_report_includes_user_claims_document_scan_and_disclaimers():
    response = client.post("/api/investigate/report", json={
        "conversation_history": [
            {"role": "user", "content": "I want to buy agricultural land near Shadnagar."},
            {"role": "assistant", "content": "Have you spoken with a broker?"},
            {"role": "user", "content": "The broker says the title is clear. I have a deed."},
        ],
        "document_analyses": [{
            "filename": "seller-deed.txt",
            "total_characters": 120,
            "overall_risk_score": 55,
            "risk_level": "HIGH",
            "detected_issues": [{
                "issue_title": "Mortgage reference",
                "risk_level": "HIGH",
                "snippet": "Loan account mentioned",
                "explanation": "A text pattern mentions a possible loan; current status is not known.",
                "lawyer_questions": ["Is a registered discharge deed available?"],
            }],
            "summary": "Text-pattern scan found a possible loan reference.",
            "survey_numbers_found": ["SY-123"],
            "encumbrance_clauses_found": True,
            "disclaimer": "This scan does not verify title or document authenticity.",
            "evidence_type": "USER_PROVIDED_DOCUMENT_TEXT",
            "ai_mode": "RULE_BASED_DOCUMENT_SCAN",
        }],
    })

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    from io import BytesIO
    from pypdf import PdfReader

    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(response.content)).pages)
    assert "Buyer requirements and preferences" in text
    assert "Broker or seller claims and evidence status" in text
    assert "UNVERIFIED" in text
    assert "seller-deed.txt" in text
    assert "Mortgage reference" in text
    assert "NO_VERIFIED_LISTING_FEED" in text
    assert "not independently verified" in text.lower()


def test_conversation_report_requires_user_input_and_rejects_unknown_parcel():
    empty = client.post("/api/investigate/report", json={"conversation_history": []})
    assert empty.status_code == 400

    invalid_parcel = client.post("/api/investigate/report", json={
        "conversation_history": [{"role": "user", "content": "I want to buy land."}],
        "selected_land_id": "not-a-demo-parcel",
    })
    assert invalid_parcel.status_code == 404


def test_conversation_report_marks_local_script_text_that_its_font_cannot_render():
    from io import BytesIO
    from pypdf import PdfReader

    response = client.post("/api/investigate/report", json={
        "conversation_history": [{"role": "user", "content": "నాకు భూమి కొనాలి"}],
    })

    assert response.status_code == 200
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(response.content)).pages)
    assert "Original-language text is not supported by this PDF font" in text
    assert "■■■" not in text


def test_broker_claim_report_uses_claim_specific_checks_and_missing_information_status():
    from app.services.reasoning_service import reasoning_service

    statement = "The broker says the seller owns this land and a highway is coming nearby."
    missing_report = reasoning_service._build_case_report(statement, [], None, [])
    missing_claim = missing_report["broker_claims"][0]
    assert missing_claim["status"] == "MISSING_INFORMATION"
    assert any("chain of title" in check for check in missing_claim["required_checks"])
    assert any("official government order" in check for check in missing_claim["required_checks"])

    scanned_document = {
        "filename": "seller-deed.txt",
        "survey_numbers_found": ["SY-123"],
    }
    supplied_report = reasoning_service._build_case_report(
        statement, [], None, [scanned_document]
    )
    supplied_claim = supplied_report["broker_claims"][0]
    assert supplied_claim["status"] == "UNVERIFIED"
    assert any("alignment" in check for check in supplied_claim["required_checks"])


def test_broker_claim_answer_is_remembered_after_follow_up_questions():
    from app.services.reasoning_service import reasoning_service

    history = [
        {"role": "user", "content": "I want to buy agricultural land near Shadnagar."},
        {"role": "assistant", "content": "Have you already approached a broker?"},
        {"role": "user", "content": "Yes."},
        {"role": "assistant", "content": "What did the broker tell you about the land?"},
    ]
    claim = "He offered 5 acres at 25 lakhs per acre and says there are no legal problems."
    context = reasoning_service._build_buyer_context(claim, history)
    assert context["broker_status"] == "YES"
    assert claim in context["broker_statements"]
    assert context["next_missing_detail"] == "the village and survey/subdivision number, if known"

    next_history = history + [
        {"role": "user", "content": claim},
        {"role": "assistant", "content": "Do you know the survey or subdivision number?"},
    ]
    after_survey_answer = reasoning_service._build_buyer_context(
        "I don't know the survey number.", next_history
    )
    assert claim in after_survey_answer["broker_statements"]
    assert after_survey_answer["next_missing_detail"] == "land type"


def test_collaborative_investigation_telugu():
    response = client.post("/api/investigate/collaborate", json={
        "query": "Check a Telugu land parcel.",
        "conversation_language": "te",
    })
    assert response.status_code == 503
    assert "no external LLM provider has been selected" in response.json()["detail"]
def test_all_spoken_investigation_turns_use_the_single_bhoomi_voice(monkeypatch):
    from app.api import routes_investigate

    document_scan = {
        "filename": "title.txt",
        "total_characters": 100,
        "overall_risk_score": 10,
        "risk_level": "LOW",
        "detected_issues": [],
        "summary": "Text-pattern scan only.",
        "survey_numbers_found": [],
        "encumbrance_clauses_found": False,
        "disclaimer": "Not legal verification.",
        "evidence_type": "USER_PROVIDED_DOCUMENT_TEXT",
        "ai_mode": "RULE_BASED_DOCUMENT_SCAN",
    }
    investigate = AsyncMock(return_value={
        "user_query": "Check this parcel.",
        "conversation_language": "en",
        "matched_land_ids": [],
        "dialogue_sequence": [
            {
                "character": character,
                "character_name": character.title(),
                "role": "Investigation contributor",
                "text": f"{character.title()} response.",
                "voice_id": "",
                "evidence_badge": "Synthetic demo data",
            }
            for character in ("bhoomi", "nyaya", "infra", "amma", "bhoomi")
        ],
        "model_used": "test-provider",
        "provider": "TEST_PROVIDER",
        "is_live": True,
        "overall_risk_level": "NOT_ASSESSED",
    })
    monkeypatch.setattr(routes_investigate.reasoning_service, "investigate_collaborative", investigate)
    speak = AsyncMock(return_value=("audio", "GNANI_TIMBRE_V2.5", 1.0, "Trupti", True))
    monkeypatch.setattr(routes_investigate.timbre_service, "speak", speak)

    response = client.post("/api/investigate/collaborate", json={
        "query": "Check this parcel.",
        "conversation_language": "en",
        "conversation_history": [
            {"role": "user", "content": "I am considering the parcel near Keesara."},
            {"role": "assistant", "content": "Which title papers have you received?"},
        ],
        "document_analyses": [document_scan],
    })

    assert response.status_code == 200
    assert investigate.await_args.kwargs["conversation_history"] == [
        {"role": "user", "content": "I am considering the parcel near Keesara."},
        {"role": "assistant", "content": "Which title papers have you received?"},
    ]
    assert investigate.await_args.kwargs["document_analyses"] == [document_scan]
    assert speak.await_count == 0
    dialogue = response.json()["dialogue_sequence"]
    assert dialogue[0]["audio_base64"] is None
    assert dialogue[-1]["audio_base64"] is None

def test_investigation_rejects_empty_question():
    response = client.post("/api/investigate/collaborate", json={
        "query": "   ",
        "conversation_language": "en",
    })
    assert response.status_code == 422

def test_investigation_rejects_unknown_selected_land():
    response = client.post("/api/investigate/collaborate", json={
        "query": "Is this land safe?",
        "conversation_language": "en",
        "selected_land_id": "not-a-demo-parcel",
    })
    assert response.status_code == 404

def test_switch_reasoning_provider():
    res = client.post("/api/investigate/provider", json={"provider": "EXTERNAL_TEST_PROVIDER"})
    assert res.status_code == 200
    data = res.json()
    assert data["new_provider"] == "EXTERNAL_TEST_PROVIDER"

@pytest.mark.asyncio
async def test_speech_status_requires_a_successful_provider_request(monkeypatch):
    from app.config import settings
    from app.services.prisma_service import prisma_service
    from app.services.timbre_service import timbre_service

    monkeypatch.setattr(settings, "mock_mode", False)
    monkeypatch.setattr(prisma_service, "mock_mode", False)
    monkeypatch.setattr(timbre_service, "mock_mode", False)
    monkeypatch.setattr(prisma_service, "api_key", "test-key")
    monkeypatch.setattr(timbre_service, "api_key", "test-key")
    monkeypatch.setattr(prisma_service, "last_ping_status", "UNKNOWN")
    monkeypatch.setattr(timbre_service, "last_ping_status", "UNKNOWN")

    prisma = await prisma_service.check_health()
    timbre = await timbre_service.check_health()
    assert prisma.connection_status == "CONFIGURED_UNVERIFIED"
    assert timbre.connection_status == "CONFIGURED_UNVERIFIED"
    assert prisma.is_live is False
    assert timbre.is_live is False

    monkeypatch.setattr(prisma_service, "last_ping_status", "REQUEST_SUCCEEDED")
    monkeypatch.setattr(timbre_service, "last_ping_status", "REQUEST_SUCCEEDED")
    assert (await prisma_service.check_health()).connection_status == "CONNECTED"
    assert (await timbre_service.check_health()).connection_status == "CONNECTED"

@pytest.mark.asyncio
async def test_unselected_reasoning_provider_stays_unconfigured(monkeypatch):
    from app.config import settings
    from app.services.ai_errors import ProviderUnavailableError
    from app.services.reasoning_service import reasoning_service

    monkeypatch.setattr(settings, "reasoning_provider", "")
    monkeypatch.setattr(reasoning_service, "provider", "")
    status = await reasoning_service.check_health()
    assert status.connection_status == "NOT_CONFIGURED"
    assert status.provider == "UNCONFIGURED"

    with pytest.raises(ProviderUnavailableError, match="no external LLM provider has been selected"):
        await reasoning_service.reason("Check this parcel.")
def test_buyer_context_retains_preferences_claims_documents_and_concerns():
    from app.services.reasoning_service import reasoning_service

    history = [
        {"role": "user", "content": "I want to buy land near Hyderabad."},
        {"role": "assistant", "content": "Which type of land?"},
        {"role": "user", "content": "Agricultural land, around 5 acres."},
        {"role": "assistant", "content": "What is your budget?"},
        {"role": "user", "content": "I spoke with a broker."},
        {
            "role": "user",
            "content": "My budget is 50 lakh. The broker promised returns; I have not seen the title documents and worry about a loan.",
        },
    ]

    context = reasoning_service._build_buyer_context("Anything else?", history)

    assert context["buying_intent"] is True
    assert context["preferred_location"] == "Hyderabad"
    assert context["land_type"] == "Agricultural land"
    assert context["acreage"] == "5 acres"
    assert context["budget"] == "50 lakh"
    assert context["broker_statements"]
    assert context["documents_discussed"]
    assert context["concerns"]
    assert context["next_missing_detail"] is None


def test_buyer_context_splits_broker_path_from_yes_or_no_answer():
    from app.services.reasoning_service import reasoning_service

    history = [
        {"role": "user", "content": "I want to buy land near Shadnagar."},
        {"role": "assistant", "content": "Have you already approached a broker?"},
    ]

    broker = reasoning_service._build_buyer_context("Yes", history)
    independent = reasoning_service._build_buyer_context("No, not yet", history)

    assert broker["broker_status"] == "YES"
    assert broker["next_missing_detail"] == "what the broker said about the parcel"
    assert independent["broker_status"] == "NO"
    assert independent["next_missing_detail"] == "land type"

    later_turn = reasoning_service._build_buyer_context(
        "Agricultural land",
        [
            *history,
            {"role": "user", "content": "No, not yet."},
            {"role": "assistant", "content": "What type of land are you looking for?"},
        ],
    )
    assert later_turn["broker_status"] == "NO"
    assert later_turn["next_missing_detail"] == "required acreage"


def test_broker_price_is_not_mistaken_for_buyer_budget():
    from app.services.reasoning_service import reasoning_service

    context = reasoning_service._build_buyer_context(
        "The broker showed me 5 acres near Shadnagar for 25 lakhs per acre and says the title is clear.",
        [
            {"role": "user", "content": "I want to buy land near Shadnagar."},
            {"role": "assistant", "content": "Have you already approached a broker?"},
            {"role": "user", "content": "Yes."},
            {"role": "assistant", "content": "What did the broker say?"},
        ],
    )

    assert context["broker_status"] == "YES"
    assert context["acreage"] == "5 acres"
    assert context["asking_price_per_acre"] == "25 lakhs"
    assert context["budget"] is None
    assert context["next_missing_detail"] == "whether the broker supplied documents or a survey number"


def test_synthetic_infrastructure_claim_is_never_verified():
    response = client.post("/api/claims/check", json={
        "statement": "The Regional Ring Road is officially announced near the land.",
        "land_id": "bv-hyd-01",
        "language": "en",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["verification_status"] == "UNVERIFIED"
    assert data["confidence_level"] == "Low"
    assert data["evidence_type"] == "SYNTHETIC_DEMONSTRATION_DATA"
    assert "did not query government portals" in data["explanation"]
