import logging
import time
import mimetypes
import httpx
from typing import Tuple, Dict, Any
from app.config import settings
from app.models.ai import ModelStatusItem
from app.services.ai_errors import ProviderRequestError, ProviderUnavailableError

logger = logging.getLogger(__name__)

class PrismaService:
    """
    Gnani Prisma v2.5 / v3.0 Speech-to-Text (STT) Integration Service.
    Official Documentation: https://docs.gnani.ai/api/introduction/introduction
    Official Endpoint: https://api.vachana.ai/stt/v3
    Header: X-API-Key-ID: <GNANI_API_KEY>
    """

    SUPPORTED_LANGUAGES = [
        "te", "hi", "en", "ta", "kn", "ml", "mr", "bn", "gu", "pa"
    ]

    @staticmethod
    def normalize_language_code(language_code: str) -> str:
        normalized = (language_code or "").strip().lower()
        if not normalized:
            return "te"
        if "-" in normalized:
            normalized = normalized.split("-", 1)[0]
        return normalized

    def __init__(self):
        self.api_url = settings.prisma_api_url
        self.api_key = settings.gnani_api_key
        self.mock_mode = settings.mock_mode
        self.last_response_time_ms = 0.0
        self.last_ping_status = "UNKNOWN"

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language_code: str | None = None
    ) -> Tuple[str, str, str, bool]:
        """
        Transcribes audio bytes to text.
        Returns: (transcribed_text, detected_language, ai_mode, is_live)
        """
        start_time = time.time()

        if self.mock_mode:
            raise ProviderUnavailableError(
                "Speech recognition is disabled in mock mode. Configure Gnani credentials and set MOCK_MODE=false."
            )
        if not self.api_key:
            raise ProviderUnavailableError("GNANI_API_KEY is required to use Gnani Prisma.")
        if not audio_bytes:
            raise ProviderRequestError("The uploaded audio file is empty.")

        headers = {
            "X-API-Key-ID": self.api_key,
            "Accept": "application/json"
        }

        normalized_language = (language_code or "").strip().lower()
        if not normalized_language or normalized_language in {"auto", "indic-auto", "detect", "auto-detect"}:
            gnani_lang = "indic-auto"
        else:
            normalized_language = self.normalize_language_code(language_code)
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
                raise ProviderRequestError(
                    f"Unsupported Prisma language '{language_code}'. Choose one of: {', '.join(lang_mapping)} or use indic-auto."
                )

        try:
            async with httpx.AsyncClient(timeout=settings.prisma_timeout_seconds) as client:
                files = {
                    "audio_file": (
                        filename,
                        audio_bytes,
                        mimetypes.guess_type(filename)[0] or "application/octet-stream",
                    )
                }
                data = {
                    "model": "prisma-v3.0",
                    "language_code": gnani_lang,
                }

                logger.info(f"Calling Gnani Prisma API at {self.api_url} using language hint '{gnani_lang}'")
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    files=files,
                    data=data
                )
                self.last_response_time_ms = round((time.time() - start_time) * 1000, 1)

                if response.status_code == 200:
                    resp_data = response.json()
                    transcript = resp_data.get("transcript")
                    if resp_data.get("success") is not True or not isinstance(transcript, str) or not transcript.strip():
                        self.last_ping_status = "INVALID_RESPONSE"
                        raise ProviderRequestError("Gnani Prisma returned no usable transcription.")
                    detected_lang = resp_data.get("detected_language_code")
                    if not isinstance(detected_lang, str) or not detected_lang.strip():
                        self.last_ping_status = "INVALID_RESPONSE"
                        raise ProviderRequestError("Gnani Prisma did not identify the transcription language.")
                    self.last_ping_status = "REQUEST_SUCCEEDED"
                    return transcript.strip(), detected_lang, "GNANI_PRISMA_V3.0", True
                else:
                    self.last_ping_status = f"ERROR_{response.status_code}"
                    logger.error("Gnani Prisma request failed with status %s", response.status_code)
                    raise ProviderRequestError(
                        f"Gnani Prisma rejected the transcription request (HTTP {response.status_code})."
                    )

        except (ProviderRequestError, ProviderUnavailableError):
            raise
        except httpx.TimeoutException as e:
            self.last_response_time_ms = round((time.time() - start_time) * 1000, 1)
            self.last_ping_status = "REQUEST_TIMEOUT"
            logger.warning("Gnani Prisma transcription timed out after %s seconds", settings.prisma_timeout_seconds)
            raise ProviderUnavailableError(
                f"Gnani Prisma transcription timed out after {settings.prisma_timeout_seconds:g} seconds. Try a shorter recording or retry."
            ) from e
        except Exception as e:
            logger.exception("Gnani Prisma transcription request failed")
            self.last_response_time_ms = round((time.time() - start_time) * 1000, 1)
            self.last_ping_status = "CONNECTION_EXCEPTION"
            raise ProviderUnavailableError("Gnani Prisma could not be reached. Check the service and try again.") from e

    async def check_health(self) -> ModelStatusItem:
        if self.mock_mode:
            return ModelStatusItem(
                model_name="Gnani Prisma v3.0",
                provider="MOCK_MODE",
                role="STT",
                connection_status="MOCK_MODE",
                is_live=False,
                endpoint=self.api_url,
                last_ping_status="NOT_PROBED",
                supported_languages=self.SUPPORTED_LANGUAGES,
                note="Speech recognition is disabled in mock mode; no transcription is generated. To enable it, set MOCK_MODE=false and configure GNANI_API_KEY."
            )

        configured = bool(self.api_key)
        connected = configured and self.last_ping_status == "REQUEST_SUCCEEDED"
        failed = self.last_ping_status not in {"UNKNOWN", "REQUEST_SUCCEEDED"}
        return ModelStatusItem(
            model_name="Gnani Prisma v3.0",
            provider="GNANI_AI",
            role="STT",
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
                "A successful transcription request verified this provider."
                if connected else
                "The last transcription request failed; availability was not verified."
                if failed else
                "GNANI_API_KEY is configured, but connectivity is not yet verified by a transcription request."
                if configured else
                "GNANI_API_KEY is required. Set MOCK_MODE=false to enable Prisma requests."
            )
        )

prisma_service = PrismaService()
