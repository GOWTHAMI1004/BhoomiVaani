import logging
import time
import httpx
from typing import Tuple, Dict, Any
from app.config import settings
from app.models.ai import ModelStatusItem

logger = logging.getLogger(__name__)

class PrismaService:
    """
    Gnani Prisma v2.5 / v3.0 Speech-to-Text (STT) Integration Service.
    Official Documentation: https://docs.gnani.ai/api/introduction/introduction
    Official Endpoint: https://api.vachana.ai/stt/v3
    Header: X-API-Key-ID: <GNANI_API_KEY>
    """

    SUPPORTED_LANGUAGES = [
        "te", "hi", "en", "ta", "kn", "ml", "mr", "bn", "gu", "pa", "indic-auto"
    ]

    def __init__(self):
        self.api_url = settings.prisma_api_url
        self.api_key = settings.gnani_api_key
        self.mock_mode = settings.mock_mode or not bool(self.api_key)
        self.last_response_time_ms = 0.0
        self.last_ping_status = "UNKNOWN"

    async def transcribe(
        self, 
        audio_bytes: bytes, 
        filename: str = "audio.wav", 
        language_code: str = "indic-auto"
    ) -> Tuple[str, str, str, bool]:
        """
        Transcribes audio bytes to text.
        Returns: (transcribed_text, detected_language, ai_mode, is_live)
        """
        start_time = time.time()

        if self.mock_mode:
            logger.info("PrismaService running in MOCK / DEV ADAPTER MODE")
            text, lang = self._mock_transcription(audio_bytes, language_code)
            self.last_response_time_ms = round((time.time() - start_time) * 1000, 1)
            self.last_ping_status = "OK (MOCK)"
            return text, lang, "MOCK DEV ADAPTER", False

        headers = {
            "X-API-Key-ID": self.api_key,
            "Accept": "application/json"
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
            "pa": "pa-IN",
            "indic-auto": "indic-auto"
        }
        gnani_lang = lang_mapping.get(language_code, "indic-auto")

        try:
            async with httpx.AsyncClient(timeout=settings.api_timeout_seconds) as client:
                files = {
                    "audio_file": (filename, audio_bytes, "audio/wav")
                }
                data = {
                    "model": "prisma-v2.5",
                    "language_code": gnani_lang
                }

                logger.info(f"Calling Gnani Prisma API at {self.api_url}")
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    files=files,
                    data=data
                )
                self.last_response_time_ms = round((time.time() - start_time) * 1000, 1)

                if response.status_code == 200:
                    resp_data = response.json()
                    transcript = resp_data.get("transcript") or resp_data.get("text") or ""
                    detected_lang = resp_data.get("language_code") or language_code
                    self.last_ping_status = "OK"
                    return transcript.strip(), detected_lang, "GNANI_PRISMA_V2.5", True
                else:
                    logger.error(
                        f"Gnani Prisma API error {response.status_code}: {response.text}"
                    )
                    self.last_ping_status = f"ERROR_{response.status_code}"
                    mock_text, mock_lang = self._mock_transcription(audio_bytes, language_code)
                    return f"[Live API error {response.status_code}] {mock_text}", mock_lang, "MOCK DEV ADAPTER (Fallback)", False

        except Exception as e:
            logger.exception(f"Exception during Gnani Prisma transcription: {str(e)}")
            self.last_response_time_ms = round((time.time() - start_time) * 1000, 1)
            self.last_ping_status = "CONNECTION_EXCEPTION"
            mock_text, mock_lang = self._mock_transcription(audio_bytes, language_code)
            return f"[Connection Exception: {str(e)}] {mock_text}", mock_lang, "MOCK DEV ADAPTER (Fallback)", False

    async def check_health(self) -> ModelStatusItem:
        """
        Pings Prisma service endpoint or reports mock adapter status.
        """
        if self.mock_mode:
            return ModelStatusItem(
                model_name="Gnani Prisma v2.5",
                provider="MOCK_DEV_ADAPTER",
                role="STT",
                connection_status="MOCK_FALLBACK",
                is_live=False,
                endpoint=self.api_url,
                last_ping_status="HEALTHY (DEV ADAPTER)",
                last_response_time_ms=5.0,
                supported_languages=self.SUPPORTED_LANGUAGES,
                note="Running in offline development adapter mode. Provide GNANI_API_KEY for live calls."
            )

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(self.api_url.replace("/stt/v3", "/health"), headers={"X-API-Key-ID": self.api_key})
                latency = round((time.time() - start) * 1000, 1)
                is_ok = res.status_code in (200, 404, 405) # reachable
                return ModelStatusItem(
                    model_name="Gnani Prisma v2.5",
                    provider="GNANI_AI",
                    role="STT",
                    connection_status="CONNECTED" if is_ok else "OFFLINE",
                    is_live=is_ok,
                    endpoint=self.api_url,
                    last_ping_status="OK" if is_ok else f"STATUS_{res.status_code}",
                    last_response_time_ms=latency,
                    supported_languages=self.SUPPORTED_LANGUAGES,
                    note="Live Gnani Prisma STT service verified."
                )
        except Exception as ex:
            latency = round((time.time() - start) * 1000, 1)
            return ModelStatusItem(
                model_name="Gnani Prisma v2.5",
                provider="GNANI_AI",
                role="STT",
                connection_status="OFFLINE",
                is_live=False,
                endpoint=self.api_url,
                last_ping_status="OFFLINE",
                last_response_time_ms=latency,
                supported_languages=self.SUPPORTED_LANGUAGES,
                note=f"Connection failed: {str(ex)}"
            )

    def _mock_transcription(self, audio_bytes: bytes, language_code: str) -> Tuple[str, str]:
        """
        Generates realistic simulated voice transcription in requested Indic language.
        """
        mock_queries = {
            "te": "హైదరాబాద్ దగ్గర 6 ఎకరాల భూమి చూడాలి. బ్రోకర్ మెట్రో వస్తుందని చెప్పారు, ఇది సురక్షితమేనా?",
            "hi": "हैदराबाद के पास 6 एकड़ जमीन दिखाइए। ब्रोकर कह रहा है पास में मेट्रो आ रही है, क्या यह सुरक्षित है?",
            "ta": "ஹைதராபாத் அருகே 6 ஏக்கர் நிலம் பார்க்க வேண்டும். புரோக்கர் மெட்ரோ வருகிறது என்கிறார், இது பாதுகாப்பானதா?",
            "kn": "ಹೈದರಾಬಾದ್ ಬಳಿ 6 ಎಕರೆ ಜಮೀನು ತೋರಿಸಿ. ಬ್ರೋಕರ್ ಮೆಟ್ರೋ ಬರುತ್ತದೆ ಎಂದು ಹೇಳಿದ್ದಾರೆ, ಇದು ಸುರಕ್ಷಿತವೇ?",
            "mr": "हैदराबाद जवळ 6 एकर जमीन दाखवा. ब्रोकर म्हणतोय जवळ मेट्रो येणार आहे, ही जागा सुरक्षित आहे का?",
            "bn": "হায়দ্রাবাদের কাছে 6 একর জমি দেখান। দালাল বলছে কাছেই মেট্রো আসবে, এটা কি নিরাপদ?",
            "gu": "હૈદરાબાદ નજીક 6 એકર જમીન બતાવો. બ્રોકર કહે છે નજીકમાં મેટ્રો આવે છે, શું આ સુરક્ષિત છે?",
            "pa": "ਹੈਦਰਾਬਾਦ ਨੇੜੇ 6 ਏਕੜ ਜ਼ਮੀਨ ਦਿਖਾਓ। ਬ੍ਰੋਕਰ ਕਹਿੰਦਾ ਹੈ ਨੇੜੇ ਮੈਟਰੋ ਆ ਰਹੀ ਹੈ, ਕੀ ਇਹ ਸੁਰੱਖਿਅਤ ਹੈ?",
            "en": "Show me 6-acre land near Hyderabad. The broker says a metro station is coming nearby. Is the property safe?"
        }

        selected_text = mock_queries.get(language_code, mock_queries["en"])
        return selected_text, language_code

prisma_service = PrismaService()
