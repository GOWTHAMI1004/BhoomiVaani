import logging
import io
import wave
import math
import struct
import base64
import time
import httpx
from typing import Tuple, Dict, Optional
from app.config import settings
from app.models.ai import ModelStatusItem

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

    CHARACTER_VOICES = {
        "bhoomi": {"voice": "Nalini", "speed": 1.0, "pitch": 1.05},
        "nyaya": {"voice": "Aditya", "speed": 0.95, "pitch": 0.90},
        "infra": {"voice": "Kabir", "speed": 1.05, "pitch": 1.0},
        "amma": {"voice": "Kalyani", "speed": 0.90, "pitch": 0.85}
    }

    def __init__(self):
        self.api_url = settings.timbre_api_url
        self.api_key = settings.gnani_api_key
        self.mock_mode = settings.mock_mode or not bool(self.api_key)
        self.last_response_time_ms = 0.0
        self._audio_cache: Dict[str, Tuple[str, float]] = {} # (text, lang, char) -> (b64, duration)

    async def speak(
        self,
        text: str,
        language: str = "te",
        character: str = "bhoomi",
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> Tuple[str, str, float, str, bool]:
        """
        Synthesizes text to speech using character-specific voice settings.
        Returns: (base64_audio_data, ai_mode, duration_sec, voice_used, is_live)
        """
        start = time.time()
        char_config = self.CHARACTER_VOICES.get(character.lower(), self.CHARACTER_VOICES["bhoomi"])
        voice_id = voice or char_config["voice"]

        cache_key = f"{character}:{language}:{text[:80]}"
        if cache_key in self._audio_cache:
            b64, dur = self._audio_cache[cache_key]
            return b64, "TIMBRE_CACHED", dur, voice_id, not self.mock_mode

        if self.mock_mode:
            logger.info(f"TimbreService generating character audio in MOCK MODE for character '{character}'")
            b64, dur = self._generate_character_mock_wav(character, text)
            self._audio_cache[cache_key] = (b64, dur)
            self.last_response_time_ms = round((time.time() - start) * 1000, 1)
            return b64, "MOCK DEV ADAPTER", dur, voice_id, False

        headers = {
            "X-API-Key-ID": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/wav, application/json"
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
        gnani_lang = lang_mapping.get(language, "te-IN")

        payload = {
            "text": text[:600],
            "voice": voice_id,
            "model": "timbre-v2.5",
            "language": gnani_lang,
            "speed": speed or char_config["speed"]
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
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        data = response.json()
                        b64 = data.get("audio_content") or data.get("audio_base64") or ""
                        dur = float(data.get("duration", 3.0))
                    else:
                        raw_bytes = response.content
                        b64 = base64.b64encode(raw_bytes).decode("utf-8")
                        dur = max(1.5, round(len(raw_bytes) / 32000, 2))

                    self._audio_cache[cache_key] = (b64, dur)
                    return b64, "GNANI_TIMBRE_V2.5", dur, voice_id, True
                else:
                    logger.error(f"Timbre API error {response.status_code}: {response.text}")
                    b64, dur = self._generate_character_mock_wav(character, text)
                    return b64, "MOCK DEV ADAPTER (Fallback)", dur, voice_id, False

        except Exception as e:
            logger.exception(f"Exception during Gnani Timbre TTS: {str(e)}")
            self.last_response_time_ms = round((time.time() - start) * 1000, 1)
            b64, dur = self._generate_character_mock_wav(character, text)
            return b64, "MOCK DEV ADAPTER (Fallback)", dur, voice_id, False

    async def check_health(self) -> ModelStatusItem:
        if self.mock_mode:
            return ModelStatusItem(
                model_name="Gnani Timbre v2.5",
                provider="MOCK_DEV_ADAPTER",
                role="TTS",
                connection_status="MOCK_FALLBACK",
                is_live=False,
                endpoint=self.api_url,
                last_ping_status="HEALTHY (DEV ADAPTER)",
                last_response_time_ms=3.0,
                supported_languages=self.SUPPORTED_LANGUAGES,
                note="Offline speech synthesizer adapter. Configured with 4 distinct character voice acoustic profiles."
            )

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(self.api_url.replace("/tts/inference", "/health"), headers={"X-API-Key-ID": self.api_key})
                latency = round((time.time() - start) * 1000, 1)
                ok = res.status_code in (200, 404, 405)
                return ModelStatusItem(
                    model_name="Gnani Timbre v2.5",
                    provider="GNANI_AI",
                    role="TTS",
                    connection_status="CONNECTED" if ok else "OFFLINE",
                    is_live=ok,
                    endpoint=self.api_url,
                    last_ping_status="OK" if ok else f"STATUS_{res.status_code}",
                    last_response_time_ms=latency,
                    supported_languages=self.SUPPORTED_LANGUAGES,
                    note="Live Gnani Timbre multilingual TTS service connected."
                )
        except Exception as e:
            return ModelStatusItem(
                model_name="Gnani Timbre v2.5",
                provider="GNANI_AI",
                role="TTS",
                connection_status="OFFLINE",
                is_live=False,
                endpoint=self.api_url,
                last_ping_status="CONNECTION_FAILED",
                last_response_time_ms=0.0,
                supported_languages=self.SUPPORTED_LANGUAGES,
                note=f"Timbre API connection error: {str(e)}"
            )

    def _generate_character_mock_wav(self, character: str, text: str) -> Tuple[str, float]:
        """
        Synthesizes character-specific PCM audio waves in Python wave library.
        Provides distinct, audible, pleasant tones for each of the 4 characters.
        """
        sample_rate = 16000
        duration = min(3.5, max(1.8, len(text) * 0.035))
        total_samples = int(sample_rate * duration)

        # Character Frequency Signatures:
        # Bhoomi: Friendly, welcoming guide (C5 -> E5 -> G5)
        # Nyaya: Deep, analytical legal mind (A3 -> E4 -> A4)
        # Infra: Technical, energetic explorer (D4 -> G4 -> B4)
        # Amma: Warm, maternal protective elder (G3 -> B3 -> D4)
        chords = {
            "bhoomi": [523.25, 659.25, 783.99, 1046.50],
            "nyaya":  [220.00, 329.63, 440.00, 329.63],
            "infra":  [293.66, 392.00, 493.88, 587.33],
            "amma":   [196.00, 246.94, 293.66, 392.00]
        }
        frequencies = chords.get(character.lower(), chords["bhoomi"])
        samples_per_note = total_samples // len(frequencies)

        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            for i in range(total_samples):
                note_idx = min(i // samples_per_note, len(frequencies) - 1)
                freq = frequencies[note_idx]
                note_progress = (i % samples_per_note) / samples_per_note

                decay = math.exp(-2.5 * note_progress)
                sine_val = math.sin(2 * math.pi * freq * (i / sample_rate))
                harmonic_val = 0.25 * math.sin(4 * math.pi * freq * (i / sample_rate))

                amplitude = 16000 * decay * (sine_val + harmonic_val)
                clamped_amp = max(-32767, min(32767, int(amplitude)))
                wav_file.writeframes(struct.pack("<h", clamped_amp))

        wav_bytes = wav_io.getvalue()
        b64_str = base64.b64encode(wav_bytes).decode("utf-8")
        return b64_str, duration

timbre_service = TimbreService()
