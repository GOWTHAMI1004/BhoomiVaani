import httpx
import pytest

from app.config import settings
from app.services.ai_errors import ProviderUnavailableError
from app.services.prisma_service import PrismaService


@pytest.mark.asyncio
async def test_prisma_timeout_is_reported_with_its_configured_limit(monkeypatch):
    service = PrismaService()
    monkeypatch.setattr(settings, "prisma_timeout_seconds", 2.5)
    monkeypatch.setattr(service, "mock_mode", False)
    monkeypatch.setattr(service, "api_key", "test-key")

    class Client:
        def __init__(self, timeout):
            assert timeout == 2.5

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def post(self, *_args, **_kwargs):
            raise httpx.ReadTimeout("provider response timed out")

    monkeypatch.setattr("app.services.prisma_service.httpx.AsyncClient", Client)

    with pytest.raises(ProviderUnavailableError, match="timed out after 2.5 seconds"):
        await service.transcribe(b"audio bytes", "recording.wav", "auto")

    assert service.last_ping_status == "REQUEST_TIMEOUT"
