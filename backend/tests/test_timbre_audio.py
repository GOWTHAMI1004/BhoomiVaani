import base64
import struct
import wave
from io import BytesIO

import pytest

from app.services.ai_errors import ProviderRequestError, ProviderUnavailableError
from app.services.timbre_service import TimbreService


def _wav(data_size: int, pcm: bytes, sample_rate: int = 24000) -> bytes:
    return (
        b"RIFF"
        + struct.pack("<I", data_size + 36 if data_size != 0xFFFFFFFF else data_size)
        + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", data_size)
        + pcm
    )


def test_normalize_streamed_wav_chunk_lengths():
    audio = _wav(0xFFFFFFFF, b"\x00\x00" * 8)

    normalized = TimbreService._normalize_wav_container(audio)

    assert struct.unpack_from("<I", normalized, 4)[0] == len(normalized) - 8
    assert struct.unpack_from("<I", normalized, 40)[0] == len(normalized) - 44
    with wave.open(BytesIO(normalized), "rb") as wav:
        assert wav.getnframes() == 8
        assert wav.getframerate() == 24000


def test_normalize_valid_wav_leaves_it_unchanged():
    audio = _wav(16, b"\x00\x00" * 8)

    assert TimbreService._normalize_wav_container(audio) == audio


def test_normalize_rejects_non_wav_provider_audio():
    with pytest.raises(ProviderRequestError, match="not a valid WAV"):
        TimbreService._normalize_wav_container(b"not wav")


def test_validate_accepts_documented_48khz_mono_pcm_wav():
    audio = _wav(32, b"\x01\x00" * 16, sample_rate=48000)

    assert TimbreService._validate_wav_audio(audio) == 0.0


@pytest.mark.asyncio
async def test_timbre_sends_dynamic_text_and_returns_binary_wav(monkeypatch):
    from app.config import settings

    service = TimbreService()
    monkeypatch.setattr(service, "mock_mode", False)
    monkeypatch.setattr(service, "api_key", "test-key")
    audio = _wav(32, b"\x01\x00" * 16, sample_rate=48000)
    dynamic_reply = "Please verify the current survey map with the revenue office."

    class Response:
        status_code = 200
        content = audio
        headers = {"content-type": "audio/wav"}

    class Client:
        def __init__(self, timeout):
            assert timeout == settings.api_timeout_seconds

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def post(self, url, *, headers, json):
            assert url == "https://api.vachana.ai/api/v1/tts/inference"
            assert headers["X-API-Key-ID"] == "test-key"
            assert headers["Accept"] == "audio/wav"
            assert json["text"] == dynamic_reply
            assert json["model"] == "timbre-v2.5"
            assert json["voice"] == "Girish"
            assert json["language"] == "en-IN"
            assert json["audio_config"] == {
                "sample_rate": 48000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            }
            return Response()

    monkeypatch.setattr("app.services.timbre_service.httpx.AsyncClient", Client)
    encoded, mode, duration, voice, is_live = await service.speak(
        dynamic_reply, language="en", character="infra"
    )

    assert base64.b64decode(encoded) == audio
    assert mode == "GNANI_TIMBRE_V2.5"
    assert duration == 0.0
    assert voice == "Girish"
    assert is_live is True


@pytest.mark.asyncio
async def test_bhoomi_never_falls_back_to_a_preset_voice(monkeypatch):
    from app.services.timbre_service import voice_reference_service

    monkeypatch.setattr(voice_reference_service, "load_embedding", lambda: None)
    service = TimbreService()
    monkeypatch.setattr(service, "mock_mode", False)
    monkeypatch.setattr(service, "api_key", "test-key")

    with pytest.raises(ProviderUnavailableError, match="no preset voice will be substituted"):
        await service.speak("A dynamic response", language="en", character="bhoomi")


@pytest.mark.asyncio
async def test_bhoomi_sends_dynamic_text_with_stored_voice_clone(monkeypatch):
    from app.config import settings
    from app.services.timbre_service import voice_reference_service

    embedding = {"embedding": "test-embedding", "shape": [1, 768], "dtype": "torch.bfloat16"}
    monkeypatch.setattr(voice_reference_service, "load_embedding", lambda: embedding)
    service = TimbreService()
    monkeypatch.setattr(service, "mock_mode", False)
    monkeypatch.setattr(service, "api_key", "test-key")
    audio = _wav(32, b"\x01\x00" * 16, sample_rate=48000)

    class Response:
        status_code = 200
        content = audio
        headers = {"content-type": "audio/wav"}

    class Client:
        def __init__(self, timeout):
            assert timeout == settings.api_timeout_seconds

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def post(self, url, *, headers, json):
            assert url == "https://api.vachana.ai/api/v1/tts/inference"
            assert json["text"] == "A changing land-advice response."
            assert json["model"] == "vachana-vc-v1"
            assert json["speaker_embedding"] == embedding
            assert "voice" not in json and "language" not in json
            assert json["audio_config"]["sample_rate"] == 44100
            return Response()

    monkeypatch.setattr("app.services.timbre_service.httpx.AsyncClient", Client)
    encoded, mode, _, voice, live = await service.speak(
        "A changing land-advice response.", language="te", character="bhoomi"
    )

    assert base64.b64decode(encoded) == audio
    assert mode == "GNANI_TIMBRE_VOICE_CLONE"
    assert voice == "Bhoomi cloned voice"
    assert live is True
