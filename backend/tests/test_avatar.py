from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)


def test_avatar_status_exposes_only_availability(monkeypatch, tmp_path):
    video = tmp_path / "source.mp4"
    video.write_bytes(b"original-video")
    monkeypatch.setattr(settings, "bhoomi_intro_video_path", str(video))
    monkeypatch.setattr(settings, "lipsync_api_url", "")
    monkeypatch.setattr("app.api.routes_ai.voice_reference_service.is_configured", lambda: True)

    response = client.get("/api/ai/avatar/status")

    assert response.status_code == 200
    assert response.json() == {
        "intro_available": True,
        "live_lipsync_configured": False,
        "live_lipsync_state": "NOT_CONFIGURED",
        "live_lipsync_message": "LIPSYNC_API_URL is not configured. Timbre audio remains available without live mouth synchronization.",
        "lipsync_auth_configured": bool(settings.lipsync_api_key),
        "voice_clone_configured": True,
    }


def test_intro_serves_the_configured_source_read_only(monkeypatch, tmp_path):
    video = tmp_path / "flow-source.mp4"
    original = b"original-flow-video"
    video.write_bytes(original)
    monkeypatch.setattr(settings, "bhoomi_intro_video_path", str(video))

    response = client.get("/api/ai/avatar/intro")

    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    assert response.headers["cache-control"] == "no-store"
    assert response.content == original
    assert video.read_bytes() == original


def test_intro_defaults_to_the_requested_project_avatar():
    from pathlib import Path

    expected = Path(__file__).resolve().parents[2] / "AI_land_advisor_speaking_to_f5c2f339.mp4"
    if not expected.is_file():
        return
    assert Path(settings.bhoomi_intro_video_path).resolve() == expected.resolve()
    response = client.get("/api/ai/avatar/intro")
    assert response.status_code == 200
    assert response.content == expected.read_bytes()


def test_lipsync_requires_configured_adapter(monkeypatch):
    monkeypatch.setattr(settings, "lipsync_api_url", "")
    response = client.post(
        "/api/ai/avatar/lipsync",
        files={"audio_file": ("speech.wav", b"RIFF" + b"\0" * 4 + b"WAVE" + b"\0" * 40, "audio/wav")},
    )
    assert response.status_code == 503
    assert "LIPSYNC_API_URL" in response.json()["detail"]


def test_lipsync_sends_source_and_generated_wav_to_adapter(monkeypatch, tmp_path):
    video = tmp_path / "source.mp4"
    original = b"original-flow-video"
    video.write_bytes(original)
    monkeypatch.setattr(settings, "bhoomi_intro_video_path", str(video))
    monkeypatch.setattr(settings, "lipsync_api_url", "https://configured-adapter.invalid/lipsync")
    monkeypatch.setattr(settings, "lipsync_api_key", "adapter-test-secret")

    class AdapterResponse:
        status_code = 200
        content = b"generated-mp4"
        headers = {"content-type": "video/mp4"}

    class AdapterClient:
        def __init__(self, timeout):
            assert timeout == settings.api_timeout_seconds

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, *, headers, files):
            assert url == "https://configured-adapter.invalid/lipsync"
            assert headers == {"Authorization": "Bearer adapter-test-secret"}
            assert files["video_file"][1] == original
            assert files["audio_file"][1].startswith(b"RIFF")
            return AdapterResponse()

    monkeypatch.setattr("app.api.routes_ai.httpx.AsyncClient", AdapterClient)
    wav = b"RIFF" + b"\0" * 4 + b"WAVE" + b"\0" * 40
    response = client.post("/api/ai/avatar/lipsync", files={"audio_file": ("speech.wav", wav, "audio/wav")})

    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    assert response.content == b"generated-mp4"
    assert video.read_bytes() == original


def test_lipsync_rejects_an_async_job_response_instead_of_claiming_video_ready(monkeypatch, tmp_path):
    video = tmp_path / "source.mp4"
    video.write_bytes(b"original-flow-video")
    monkeypatch.setattr(settings, "bhoomi_intro_video_path", str(video))
    monkeypatch.setattr(settings, "lipsync_api_url", "https://configured-adapter.invalid/lipsync")

    class AdapterResponse:
        status_code = 202
        content = b'{"job_id":"pending"}'
        headers = {"content-type": "application/json"}
        text = '{"job_id":"pending"}'
        def json(self):
            return {"job_id": "pending"}

    class AdapterClient:
        def __init__(self, timeout):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *_args):
            return None
        async def post(self, *_args, **_kwargs):
            return AdapterResponse()

    monkeypatch.setattr("app.api.routes_ai.httpx.AsyncClient", AdapterClient)
    wav = b"RIFF" + b"\0" * 4 + b"WAVE" + b"\0" * 40
    response = client.post("/api/ai/avatar/lipsync", files={"audio_file": ("speech.wav", wav, "audio/wav")})

    assert response.status_code == 502
    assert "expected a completed video/mp4" in response.json()["detail"]
    assert "job_id" in response.json()["detail"]


def test_lipsync_reports_safe_provider_error_body(monkeypatch, tmp_path):
    video = tmp_path / "source.mp4"
    video.write_bytes(b"original-flow-video")
    monkeypatch.setattr(settings, "bhoomi_intro_video_path", str(video))
    monkeypatch.setattr(settings, "lipsync_api_url", "https://configured-adapter.invalid/lipsync")
    monkeypatch.setattr(settings, "lipsync_api_key", "test-private-key")

    class AdapterResponse:
        status_code = 422
        content = b'{"detail":"unsupported audio codec"}'
        headers = {"content-type": "application/json"}
        text = '{"detail":"unsupported audio codec"}'
        def json(self):
            return {"detail": "unsupported audio codec", "token": "test-private-key"}

    class AdapterClient:
        def __init__(self, timeout): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
        async def post(self, *_args, **_kwargs): return AdapterResponse()

    monkeypatch.setattr("app.api.routes_ai.httpx.AsyncClient", AdapterClient)
    wav = b"RIFF" + b"\0" * 4 + b"WAVE" + b"\0" * 40
    response = client.post("/api/ai/avatar/lipsync", files={"audio_file": ("speech.wav", wav, "audio/wav")})
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "HTTP 422" in detail and "unsupported audio codec" in detail
    assert "test-private-key" not in detail
    assert "configured-adapter.invalid" not in detail


def test_lipsync_connection_failure_reports_reason_without_secrets(monkeypatch, tmp_path):
    import httpx

    video = tmp_path / "source.mp4"
    video.write_bytes(b"original-flow-video")
    monkeypatch.setattr(settings, "bhoomi_intro_video_path", str(video))
    monkeypatch.setattr(settings, "lipsync_api_url", "https://configured-adapter.invalid/lipsync")
    monkeypatch.setattr(settings, "lipsync_api_key", "test-private-key")

    class AdapterClient:
        def __init__(self, timeout): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
        async def post(self, *_args, **_kwargs):
            raise httpx.ConnectError("DNS lookup failed for configured-adapter.invalid")

    monkeypatch.setattr("app.api.routes_ai.httpx.AsyncClient", AdapterClient)
    wav = b"RIFF" + b"\0" * 4 + b"WAVE" + b"\0" * 40
    response = client.post("/api/ai/avatar/lipsync", files={"audio_file": ("speech.wav", wav, "audio/wav")})
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "ConnectError" in detail and "DNS lookup failed" in detail
    assert "configured-adapter.invalid" not in detail
    assert "test-private-key" not in detail


def test_lipsync_timeout_is_reported(monkeypatch, tmp_path):
    import httpx

    video = tmp_path / "source.mp4"
    video.write_bytes(b"original-flow-video")
    monkeypatch.setattr(settings, "bhoomi_intro_video_path", str(video))
    monkeypatch.setattr(settings, "lipsync_api_url", "https://configured-adapter.invalid/lipsync")

    class AdapterClient:
        def __init__(self, timeout): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *_args): return None
        async def post(self, *_args, **_kwargs): raise httpx.ReadTimeout("provider timed out")

    monkeypatch.setattr("app.api.routes_ai.httpx.AsyncClient", AdapterClient)
    wav = b"RIFF" + b"\0" * 4 + b"WAVE" + b"\0" * 40
    response = client.post("/api/ai/avatar/lipsync", files={"audio_file": ("speech.wav", wav, "audio/wav")})
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"]


def test_lipsync_rejects_non_wav_audio(monkeypatch, tmp_path):
    video = tmp_path / "source.mp4"
    video.write_bytes(b"original-flow-video")
    monkeypatch.setattr(settings, "bhoomi_intro_video_path", str(video))
    monkeypatch.setattr(settings, "lipsync_api_url", "https://configured-adapter.invalid/lipsync")

    response = client.post("/api/ai/avatar/lipsync", files={"audio_file": ("speech.mp3", b"not-wav", "audio/mpeg")})

    assert response.status_code == 400
