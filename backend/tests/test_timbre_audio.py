import struct
import wave
from io import BytesIO

import pytest

from app.services.ai_errors import ProviderRequestError
from app.services.timbre_service import TimbreService


def _wav(data_size: int, pcm: bytes) -> bytes:
    return (
        b"RIFF"
        + struct.pack("<I", data_size + 36 if data_size != 0xFFFFFFFF else data_size)
        + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, 24000, 48000, 2, 16)
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
