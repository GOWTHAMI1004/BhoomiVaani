import logging
import base64
import io
import struct
import time
import wave
import httpx
from typing import Tuple, Dict, Optional
from app.config import settings
from app.models.ai import ModelStatusItem
from app.services.ai_errors import ProviderRequestError, ProviderUnavailableError

logger = logging.getLogger(__name__)

class TimbreService:
    """
    Gnani Timbre v2.5 Multilingual Text-to-Speech (TTS) Integration Service.
    Documentation: https://www.gnani.ai/text-to-speech
    Official Endpoint: https://api.vachana.ai/api/v1/tts/inference
    Header: X-API-Key-ID: <GNANI_API_KEY>
    """

    SUPPORTED_LANGUAGES = [
        "te", "hi", "en", "ta", "kn", "ml", "mr", "bn", "gu", "pa"
    ]

    @staticmethod
    def normalize_language_code(language: str) -> str:
        normalized = (language or "").strip().lower()
        if not normalized:
            return "en"
        if "-" in normalized:
            normalized = normalized.split("-", 1)[0]
        return normalized

    CHARACTER_VOICES = {
        "te": {"bhoomi": "Yukti", "nyaya": "Varuni", "infra": "Suhana", "amma": "Lehara"},
        "hi": {"bhoomi": "Nalini", "nyaya": "Deepak", "infra": "Roopesh", "amma": "Chitra"},
        "en": {"bhoomi": "Trupti", "nyaya": "Pranav", "infra": "Girish", "amma": "Kaveri"},
        "ta": {"bhoomi": "Asmita", "nyaya": "Vedika", "infra": "Trisha", "amma": "Noopur"},
        "kn": {"bhoomi": "Saanvi", "nyaya": "Kavin", "infra": "Saanvi", "amma": "Kavin"},
        "ml": {"bhoomi": "Reshma", "nyaya": "Riyaan", "infra": "Reshma", "amma": "Riyaan"},
        "mr": {"bhoomi": "Zahira", "nyaya": "Ishaan", "infra": "Zahira", "amma": "Ishaan"},
        "bn": {"bhoomi": "Kirra", "nyaya": "Dhruva", "infra": "Kirra", "amma": "Dhruva"},
        "gu": {"bhoomi": "Falak", "nyaya": "Veera", "infra": "Falak", "amma": "Veera"},
        "pa": {"bhoomi": "Mehuli", "nyaya": "Zayan", "infra": "Mehuli", "amma": "Zayan"},
    }

    def __init__(self):
        self.api_url = settings.timbre_api_url
        self.api_key = settings.gnani_api_key
        self.mock_mode = settings.mock_mode
        self.last_response_time_ms = 0.0
        self.last_ping_status = "UNKNOWN"
        self._audio_cache: Dict[str, Tuple[str, float]] = {} # (text, lang, char) -> (b64, duration)

    @staticmethod
    def _normalize_wav_container(audio_bytes: bytes) -> bytes:
        if len(audio_bytes) < 44 or audio_bytes[:4] != b"RIFF" or audio_bytes[8:12] != b"WAVE":
            raise ProviderRequestError("Gnani Timbre returned audio that is not a valid WAV container.")

        normalized = bytearray(audio_bytes)
        if struct.unpack_from("<I", normalized, 4)[0] == 0xFFFFFFFF:
            struct.pack_into("<I", normalized, 4, len(normalized) - 8)

        offset = 12
        while offset + 8 <= len(normalized):
            chunk_id = normalized[offset:offset + 4]
            chunk_size = struct.unpack_from("<I", normalized, offset + 4)[0]
            chunk_data_offset = offset + 8
            if chunk_id == b"data":
                if chunk_size == 0xFFFFFFFF:
                    struct.pack_into("<I", normalized, offset + 4, len(normalized) - chunk_data_offset)
                elif chunk_data_offset + chunk_size > len(normalized):
                    raise ProviderRequestError("Gnani Timbre returned a truncated WAV data chunk.")
                return bytes(normalized)
            if chunk_size == 0xFFFFFFFF:
                raise ProviderRequestError("Gnani Timbre returned an invalid WAV chunk size.")
            offset = chunk_data_offset + chunk_size + (chunk_size & 1)

        raise ProviderRequestError("Gnani Timbre returned a WAV file without an audio data chunk.")

    @staticmethod
    def _validate_wav_audio(audio_bytes: bytes) -> float:
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
                if (
                    wav.getnchannels() != 1
                    or wav.getsampwidth() != 2
                    or wav.getframerate() != 24000
                    or wav.getnframes() == 0
                ):
                    raise ProviderRequestError(
                        "Gnani Timbre returned WAV audio with an unexpected format."
                    )
                frames = wav.readframes(wav.getnframes())
                if not any(frames):
                    raise ProviderRequestError("Gnani Timbre returned silent audio.")
                return round(wav.getnframes() / wav.getframerate(), 2)
        except (wave.Error, EOFError) as exc:
            raise ProviderRequestError("Gnani Timbre returned an unreadable WAV response.") from exc

    async def speak(
        self,
        text: str,
        language: str = "en",
        character: str = "bhoomi",
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> Tuple[str, str, float, str, bool]:
        """
        Synthesizes text to speech using character-specific voice settings.
        Returns: (base64_audio_data, ai_mode, duration_sec, voice_used, is_live)
        """
        start = time.time()
        normalized_language = self.normalize_language_code(language)
        language_voices = self.CHARACTER_VOICES.get(normalized_language)
        if language_voices is None:
            raise ProviderRequestError(
                f"Gnani Timbre v2.5 does not support language '{language}'."
            )
        voice_id = voice or language_voices.get(character.lower(), language_voices["bhoomi"])
        if self.mock_mode:
            raise ProviderUnavailableError(
                "Speech synthesis is disabled in mock mode. Configure Gnani credentials and set MOCK_MODE=false."
            )
        if not self.api_key:
            raise ProviderUnavailableError("GNANI_API_KEY is required to use Gnani Timbre.")
        if not text.strip():
            raise ProviderRequestError("Speech text cannot be empty.")
        if len(text) > 600:
            raise ProviderRequestError("Speech text exceeds the 600-character limit.")

        cache_key = f"{character}:{normalized_language}:{voice_id}:{speed}:{text}"
        if cache_key in self._audio_cache:
            b64, dur = self._audio_cache[cache_key]
            return b64, "GNANI_TIMBRE_V2.5 (CACHED)", dur, voice_id, True

        headers = {
            "X-API-Key-ID": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/wav"
        }

        lang_mapping = {
            "te": "te-IN",
            "hi": "hi-IN",
            "en": "en-IN",
            "ta": "ta-IN",
            "kn": "kn-IN",
            "ml": "ml-IN",
            "mr": "mr-IN",
            "bn": "bn-IN",
            "gu": "gu-IN",
            "pa": "pa-IN"
        }
        gnani_lang = lang_mapping.get(normalized_language)
        if gnani_lang is None:
            raise ProviderRequestError(f"Unsupported Gnani Timbre language '{language}'.")

        payload = {
            "text": text,
            "voice": voice_id,
            "model": "timbre-v2.5",
            "language": gnani_lang,
            "speed": speed,
            "audio_config": {
                "sample_rate": 24000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=settings.api_timeout_seconds) as client:
                logger.info(f"Calling Gnani Timbre API at {self.api_url} for voice '{voice_id}'")
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                self.last_response_time_ms = round((time.time() - start) * 1000, 1)

                if response.status_code == 200:
                    if not response.content:
                        self.last_ping_status = "INVALID_RESPONSE"
                        raise ProviderRequestError("Gnani Timbre returned an empty audio response.")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    if content_type != "audio/wav":
                        self.last_ping_status = "INVALID_RESPONSE"
                        raise ProviderRequestError(
                            f"Gnani Timbre returned '{content_type or 'unknown'}' instead of audio/wav."
                        )
                    try:
                        raw_bytes = self._normalize_wav_container(response.content)
                        dur = self._validate_wav_audio(raw_bytes)
                    except ProviderRequestError:
                        self.last_ping_status = "INVALID_RESPONSE"
                        raise
                    b64 = base64.b64encode(raw_bytes).decode("utf-8")

                    self._audio_cache[cache_key] = (b64, dur)
                    self.last_ping_status = "REQUEST_SUCCEEDED"
                    return b64, "GNANI_TIMBRE_V2.5", dur, voice_id, True
                else:
                    self.last_ping_status = f"ERROR_{response.status_code}"
                    logger.error("Gnani Timbre request failed with status %s", response.status_code)
                    raise ProviderRequestError(
                        f"Gnani Timbre rejected the synthesis request (HTTP {response.status_code})."
                    )

        except (ProviderRequestError, ProviderUnavailableError):
            raise
        except Exception as e:
            logger.exception("Gnani Timbre synthesis request failed")
            self.last_response_time_ms = round((time.time() - start) * 1000, 1)
            self.last_ping_status = "CONNECTION_EXCEPTION"
            raise ProviderUnavailableError("Gnani Timbre could not be reached. Check the service and try again.") from e

    async def check_health(self) -> ModelStatusItem:
        if self.mock_mode:
            return ModelStatusItem(
                model_name="Gnani Timbre v2.5",
                provider="MOCK_MODE",
                role="TTS",
                connection_status="MOCK_MODE",
                is_live=False,
                endpoint=self.api_url,
                last_ping_status="NOT_PROBED",
                supported_languages=self.SUPPORTED_LANGUAGES,
                note="Speech synthesis is disabled in mock mode; no audio is generated. To enable it, set MOCK_MODE=false and configure GNANI_API_KEY."
            )

        configured = bool(self.api_key)
        connected = configured and self.last_ping_status == "REQUEST_SUCCEEDED"
        failed = self.last_ping_status not in {"UNKNOWN", "REQUEST_SUCCEEDED"}
        return ModelStatusItem(
            model_name="Gnani Timbre v2.5",
            provider="GNANI_AI",
            role="TTS",
            connection_status=(
                "CONNECTED" if connected else
                "REQUEST_FAILED" if failed else
                "CONFIGURED_UNVERIFIED" if configured else
                "NOT_CONFIGURED"
            ),
            is_live=connected,
            endpoint=self.api_url,
            last_ping_status=self.last_ping_status if configured else "MISSING_CREDENTIALS",
            last_response_time_ms=self.last_response_time_ms,
            supported_languages=self.SUPPORTED_LANGUAGES if configured else [],
            note=(
                "A successful synthesis request verified this provider."
                if connected else
                "The last synthesis request failed; availability was not verified."
                if failed else
                "GNANI_API_KEY is configured, but connectivity is not yet verified by a synthesis request."
                if configured else
                "GNANI_API_KEY is required. Set MOCK_MODE=false to enable Timbre requests."
            )
        )

timbre_service = TimbreService()
