import pytest

from app.services.ai_errors import ProviderRequestError
from app.services.prisma_service import PrismaService


@pytest.mark.asyncio
async def test_prisma_posts_wav_to_official_multipart_contract(monkeypatch):
    service = PrismaService()
    service.api_url = "https://api.vachana.ai/stt/v3"
    monkeypatch.setattr(service, "mock_mode", False)
    monkeypatch.setattr(service, "api_key", "test-key")

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {
                "success": True,
                "transcript": "  Check the survey map.  ",
                "detected_language_code": "en-IN",
            }

    class Client:
        def __init__(self, timeout):
            assert timeout > 0

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def post(self, url, *, headers, files, data):
            assert url == service.api_url
            assert headers["X-API-Key-ID"] == "test-key"
            assert headers["Accept"] == "application/json"
            assert files["audio_file"] == ("recording.wav", b"wav-data", "audio/wav")
            assert data == {"model": "prisma-v3.0", "language_code": "indic-auto"}
            return Response()

    monkeypatch.setattr("app.services.prisma_service.httpx.AsyncClient", Client)
    transcript, language, mode, live = await service.transcribe(
        b"wav-data", "recording.wav", "indic-auto"
    )

    assert (transcript, language, mode, live) == (
        "Check the survey map.", "en-IN", "GNANI_PRISMA_V3.0", True
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [
    {"success": True, "transcript": "  ", "detected_language_code": "en-IN"},
    {"success": False, "transcript": "not a transcript", "detected_language_code": "en-IN"},
    {"success": True, "transcript": "recognized words"},
])
async def test_prisma_rejects_unusable_transcription_responses(monkeypatch, body):
    service = PrismaService()
    monkeypatch.setattr(service, "mock_mode", False)
    monkeypatch.setattr(service, "api_key", "test-key")

    class Response:
        status_code = 200

        def json(self):
            return body

    class Client:
        def __init__(self, **_):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def post(self, *_args, **_kwargs):
            return Response()

    monkeypatch.setattr("app.services.prisma_service.httpx.AsyncClient", Client)
    with pytest.raises(ProviderRequestError, match="transcription|language"):
        await service.transcribe(b"audio", "recording.wav", "auto")
    assert service.last_ping_status == "INVALID_RESPONSE"
