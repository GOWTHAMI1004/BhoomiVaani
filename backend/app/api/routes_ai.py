import logging
import re
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, Response
from app.config import settings
from app.models.ai import AIChatRequest, AIChatResponse, SpeakRequest, SpeakResponse
from app.services.ai_errors import ProviderRequestError, ProviderUnavailableError
from app.services.prisma_service import prisma_service
from app.services.reasoning_service import reasoning_service
from app.services.timbre_service import timbre_service
from app.services.voice_reference_service import voice_reference_service
from app.services.land_service import land_service
from app.services.language_service import detect_conversation_language

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI"])
_lipsync_last_state = "NOT_PROBED"
_lipsync_last_message = "A configured adapter is unverified until it returns a completed MP4."


def _safe_lipsync_diagnostic(value: str, limit: int = 420) -> str:
    """Return useful provider diagnostics without echoing URLs, keys, or bearer tokens."""
    message = str(value or "").replace("\x00", " ").strip()
    if settings.lipsync_api_url:
        message = message.replace(settings.lipsync_api_url, "configured adapter endpoint")
        adapter_host = urlsplit(settings.lipsync_api_url).hostname
        if adapter_host:
            message = message.replace(adapter_host, "configured adapter host")
    message = re.sub(r"https?://[^\s\"'<>]+", "configured adapter endpoint", message)
    for secret in (settings.lipsync_api_key, settings.gnani_api_key, settings.reasoning_api_key):
        if secret:
            message = message.replace(secret, "[REDACTED]")
    message = re.sub(r"(?i)bearer\s+[^\s,;]+", "Bearer [REDACTED]", message)
    message = re.sub(
        r"(?i)(api[_-]?key|access[_-]?token|authorization)(\s*[=:]\s*)[^\s,;]+",
        r"\1\2[REDACTED]",
        message,
    )
    return re.sub(r"\s+", " ", message)[:limit]


def _safe_response_excerpt(result: httpx.Response) -> str:
    try:
        payload = result.json()
        if isinstance(payload, dict):
            selected = [str(payload[key]) for key in ("detail", "message", "error", "reason") if payload.get(key)]
            body = "; ".join(selected) if selected else result.text
        else:
            body = result.text
    except (ValueError, TypeError):
        body = result.text
    excerpt = _safe_lipsync_diagnostic(body)
    return excerpt or "The provider returned an empty response body."


@router.get("/avatar/status")
async def bhoomi_avatar_status():
    """Report whether the source clip and a live lip-sync adapter are available."""
    configured = bool(settings.lipsync_api_url)
    state = _lipsync_last_state if configured else "NOT_CONFIGURED"
    message = _lipsync_last_message if configured else (
        "LIPSYNC_API_URL is not configured. Timbre audio remains available without live mouth synchronization."
    )
    return {
        "intro_available": Path(settings.bhoomi_intro_video_path).is_file(),
        "live_lipsync_configured": configured,
        "live_lipsync_state": state,
        "live_lipsync_message": message,
        "lipsync_auth_configured": bool(settings.lipsync_api_key),
        "voice_clone_configured": voice_reference_service.is_configured(),
    }


@router.get("/avatar/intro")
async def get_bhoomi_intro_video():
    """Serve the original Google Flow clip as an introduction, read-only."""
    video_path = Path(settings.bhoomi_intro_video_path)
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="Bhoomi's introduction video is not available on this server.")
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename="bhoomi-introduction.mp4",
        headers={"Cache-Control": "no-store"},
    )


@router.post("/avatar/lipsync")
async def generate_bhoomi_lipsync(audio_file: UploadFile = File(...)):
    """Send original Flow video and generated speech to a configured MuseTalk-compatible GPU adapter.

    The configured adapter accepts multipart fields `video_file` and `audio_file`
    and returns a playable MP4 containing the supplied audio synchronized to the
    supplied source video. MuseTalk itself is not shipped or hosted by FastAPI.
    """
    global _lipsync_last_state, _lipsync_last_message
    if not settings.lipsync_api_url:
        raise HTTPException(status_code=503, detail="Live avatar lip-sync is not configured. Configure LIPSYNC_API_URL.")
    video_path = Path(settings.bhoomi_intro_video_path)
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="Bhoomi's source video is not available on this server.")
    if audio_file.content_type not in {"audio/wav", "audio/x-wav", "audio/wave", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Lip-sync requires the generated Timbre WAV audio.")

    audio_bytes = await audio_file.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    if len(audio_bytes) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Generated speech audio exceeds the configured upload limit.")
    if len(audio_bytes) < 44 or audio_bytes[:4] != b"RIFF" or audio_bytes[8:12] != b"WAVE":
        raise HTTPException(status_code=400, detail="The supplied speech audio is not a valid WAV file.")

    try:
        video_bytes = video_path.read_bytes()
        headers = {"Authorization": f"Bearer {settings.lipsync_api_key}"} if settings.lipsync_api_key else {}
        async with httpx.AsyncClient(timeout=settings.api_timeout_seconds) as client:
            result = await client.post(
                settings.lipsync_api_url,
                headers=headers,
                files={
                    "video_file": ("bhoomi-source.mp4", video_bytes, "video/mp4"),
                    "audio_file": (audio_file.filename or "timbre-response.wav", audio_bytes, "audio/wav"),
                },
            )
        if result.status_code >= 400:
            diagnostic = _safe_response_excerpt(result)
            _lipsync_last_state = "UNAVAILABLE"
            _lipsync_last_message = f"Adapter returned HTTP {result.status_code}: {diagnostic}"
            logger.warning("Lip-sync adapter returned HTTP %s: %s", result.status_code, diagnostic)
            raise HTTPException(status_code=502, detail=_lipsync_last_message)
        content_type = result.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if not result.content or content_type != "video/mp4":
            diagnostic = _safe_response_excerpt(result)
            _lipsync_last_state = "UNAVAILABLE"
            _lipsync_last_message = (
                f"Adapter returned {content_type or 'no content type'}; expected a completed video/mp4. {diagnostic}"
            )
            logger.warning("Lip-sync adapter returned an unsupported response: %s", _lipsync_last_message)
            raise HTTPException(status_code=502, detail=_lipsync_last_message)
        _lipsync_last_state = "AVAILABLE"
        _lipsync_last_message = "The adapter returned a completed MP4 for the latest response."
        return Response(content=result.content, media_type="video/mp4", headers={"Cache-Control": "no-store"})
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        diagnostic = _safe_lipsync_diagnostic(str(exc))
        _lipsync_last_state = "UNAVAILABLE"
        _lipsync_last_message = f"Adapter request timed out. {diagnostic}".strip()
        logger.warning("Lip-sync adapter timed out: %s", diagnostic or "no additional provider detail")
        raise HTTPException(status_code=504, detail=_lipsync_last_message) from exc
    except httpx.HTTPError as exc:
        diagnostic = _safe_lipsync_diagnostic(str(exc))
        _lipsync_last_state = "UNAVAILABLE"
        _lipsync_last_message = f"Adapter connection failed ({type(exc).__name__}). {diagnostic}".strip()
        logger.warning("Lip-sync adapter connection failed (%s): %s", type(exc).__name__, diagnostic or "no additional detail")
        raise HTTPException(status_code=502, detail=_lipsync_last_message) from exc

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_evon(req: AIChatRequest):
    """
    External reasoning chat endpoint. It returns a clear error until a provider is selected and integrated.
    Accepts a natural query and returns a response grounded in synthetic demo records.
    Optionally pre-synthesizes audio with Timbre.
    """
    try:
        available_lands = land_service.get_all()
        history_dicts = [{"role": m.role, "content": m.content} for m in req.conversation_history]
        language = detect_conversation_language(req.query, req.language)

        reasoning_res = await reasoning_service.reason(
            query=req.query,
            language=language,
            conversation_history=history_dicts,
            available_lands=available_lands,
            selected_land_id=req.selected_land_id
        )

        # Text remains available even when speech credentials are not configured.
        audio_b64 = None
        audio_available = False
        audio_error = None
        try:
            audio_b64, _, _, _, _ = await timbre_service.speak(
                text=reasoning_res["response"],
                language=language
            )
            audio_available = bool(audio_b64)
        except (ProviderRequestError, ProviderUnavailableError) as exc:
            logger.warning("Speech synthesis unavailable: %s", exc)
            audio_error = str(exc)

        return AIChatResponse(
            transcript=reasoning_res.get("transcript", req.query),
            response=reasoning_res.get("response", ""),
            language=language,
            matched_land_ids=reasoning_res.get("matched_land_ids", []),
            legal_warnings=reasoning_res.get("legal_warnings", []),
            infrastructure_findings=reasoning_res.get("infrastructure_findings", []),
            growth_insights=reasoning_res.get("growth_insights", []),
            audio_base64=audio_b64,
            audio_available=audio_available,
            audio_error=audio_error,
            ai_mode=reasoning_res.get("ai_mode", "UNCONFIGURED")
        )
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as e:
        logger.exception(f"Chat pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI chat request failed.")

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("auto")
):
    """
    Gnani Prisma v3.0 Speech-to-Text endpoint.
    Transcribes uploaded audio bytes.
    """
    try:
        allowed_extensions = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}
        filename = file.filename or "recording.wav"
        suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if f".{suffix}" not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Unsupported audio format. Use WAV, MP3, OGG, FLAC, AAC, or M4A.",
            )
        audio_bytes = await file.read()
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file provided.")
        if len(audio_bytes) > settings.max_upload_size_mb * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Audio file exceeds the configured upload limit.")

        normalized_language = (language or "").strip().lower()
        request_language = "indic-auto" if normalized_language in {"", "auto", "detect", "indic-auto", "auto-detect"} else language

        transcript, detected_lang, ai_mode, is_live = await prisma_service.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            language_code=request_language
        )

        return {
            "transcript": transcript,
            "detected_language": detected_lang,
            "ai_mode": ai_mode,
            "is_live": is_live
        }
    except HTTPException:
        raise
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as e:
        logger.exception(f"STT pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail="Transcription request failed.")

@router.post("/speak", response_model=SpeakResponse)
async def text_to_speech(req: SpeakRequest):
    """
    Gnani Timbre v2.5 Text-to-Speech endpoint.
    """
    try:
        audio_b64, ai_mode, duration, voice_used, is_live = await timbre_service.speak(
            text=req.text,
            language=req.language,
            character=req.character,
            voice=req.voice,
            speed=req.speed
        )

        return SpeakResponse(
            audio_base64=audio_b64,
            format="audio/wav",
            language=req.language,
            character=req.character,
            voice_used=voice_used,
            ai_mode=ai_mode,
            duration_estimate_sec=duration
        )
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as e:
        logger.exception(f"TTS pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail="Text-to-speech request failed.")
