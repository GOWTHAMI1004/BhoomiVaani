import httpx
import pytest

from app.services.ai_errors import ProviderRequestError, ProviderUnavailableError
from app.services.reasoning_service import ReasoningService


def make_service(handler):
    service = ReasoningService(transport=httpx.MockTransport(handler))
    service.provider = "GEMINI"
    service.api_key = "unit-test-key"
    service.api_base_url = "https://generativelanguage.googleapis.com/v1beta"
    service.model = "gemini-2.5-flash"
    service.timeout_seconds = 2
    return service


@pytest.mark.asyncio
async def test_gemini_uses_generate_content_api_and_auth_header():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["key_header"] = request.headers.get("x-goog-api-key")
        seen["body"] = __import__("json").loads(request.content)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "What is the survey number?"}]}}]})

    service = make_service(handler)
    result = await service._generate_gemini_content(
        "I want land near Shadnagar", "en",
        [{"role": "user", "content": "I want to buy land."}, {"role": "assistant", "content": "Have you spoken to a broker?"}],
        {"available_properties": [], "selected_property_id": None, "document_analyses": []},
    )

    assert result == "What is the survey number?"
    assert seen["url"] == "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    assert "key=" not in seen["url"]
    assert seen["key_header"] == "unit-test-key"
    assert seen["body"]["contents"][0]["role"] == "user"
    assert seen["body"]["contents"][1]["role"] == "model"
    assert "Respond in English" in seen["body"]["systemInstruction"]["parts"][0]["text"]


@pytest.mark.asyncio
async def test_gemini_multilingual_instruction_and_response_are_preserved():
    telugu_answer = "మీకు ఎంత విస్తీర్ణం కావాలి?"

    def handler(request):
        import json
        body = json.loads(request.content)
        assert "Respond in Telugu" in body["systemInstruction"]["parts"][0]["text"]
        assert "Telugu" in body["systemInstruction"]["parts"][0]["text"]
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": telugu_answer}]}}]})

    service = make_service(handler)
    response = await service._generate_gemini_content("నాకు భూమి కావాలి", "te", [], {})
    assert response == telugu_answer


@pytest.mark.asyncio
async def test_gemini_missing_configuration_is_explicit():
    service = ReasoningService()
    service.provider = "GEMINI"
    service.api_key = ""
    service.api_base_url = "https://generativelanguage.googleapis.com/v1beta"
    service.model = "gemini-2.5-flash"
    with pytest.raises(ProviderUnavailableError, match="REASONING_API_KEY"):
        await service._generate_gemini_content("Hello", "en", [], {})


@pytest.mark.parametrize(
    ("status_code", "message"),
    [(401, "authentication error"), (429, "rate limit"), (503, "temporarily unavailable")],
)
@pytest.mark.asyncio
async def test_gemini_http_errors_are_mapped_without_response_body(status_code, message):
    service = make_service(lambda request: httpx.Response(status_code, text="private response details"))
    with pytest.raises(ProviderRequestError, match=message) as error:
        await service._generate_gemini_content("Hello", "en", [], {})
    assert "private response details" not in str(error.value)


@pytest.mark.asyncio
async def test_gemini_timeout_is_reported_clearly():
    def handler(request):
        raise httpx.ReadTimeout("upstream timeout")

    service = make_service(handler)
    with pytest.raises(ProviderRequestError, match="timed out"):
        await service._generate_gemini_content("Hello", "en", [], {})


@pytest.mark.asyncio
async def test_unmatched_question_does_not_seed_unrelated_demo_locations(monkeypatch):
    from app.services.land_service import land_service

    service = make_service(lambda request: httpx.Response(500))
    captured = {}

    async def capture_context(query, language, history, context):
        captured.update(context)
        return "Which location are you considering?"

    monkeypatch.setattr(service, "_generate_gemini_content", capture_context)
    await service.investigate_collaborative(
        "I want to buy land. What should I check first?",
        conversation_language="en",
        available_lands=land_service.get_all(),
    )

    assert captured["available_properties"] == []
    assert captured["selected_property_id"] is None


def test_ai_chat_returns_reasoning_response_in_detected_language(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.services.reasoning_service import reasoning_service
    from app.services.timbre_service import timbre_service

    async def answer(query, language="te", conversation_history=None, available_lands=None, selected_land_id=None):
        assert language == "te"
        return {
            "transcript": query,
            "response": "మీ బడ్జెట్ ఎంత?",
            "language": language,
            "matched_land_ids": [],
            "legal_warnings": [],
            "infrastructure_findings": [],
            "growth_insights": [],
            "ai_mode": "GEMINI (gemini-2.5-flash)",
        }

    async def speech_unavailable(**kwargs):
        raise ProviderUnavailableError("Timbre is unavailable for this test.")

    monkeypatch.setattr(reasoning_service, "reason", answer)
    monkeypatch.setattr(timbre_service, "speak", speech_unavailable)
    response = TestClient(app).post("/api/ai/chat", json={"query": "నాకు భూమి కొనాలి", "language": "en"})

    assert response.status_code == 200
    assert response.json()["response"] == "మీ బడ్జెట్ ఎంత?"
    assert response.json()["language"] == "te"
    assert response.json()["ai_mode"] == "GEMINI (gemini-2.5-flash)"
