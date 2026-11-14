import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.config import settings
from app.models.ai import AIChatRequest, AIChatResponse, SpeakRequest, SpeakResponse
from app.services.ai_errors import ProviderRequestError, ProviderUnavailableError
from app.services.prisma_service import prisma_service
from app.services.evon_service import evon_service
from app.services.timbre_service import timbre_service
from app.services.land_service import land_service
from app.services.language_service import detect_conversation_language

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI"])

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_evon(req: AIChatRequest):
    """
    Mandatory Evon v3.3 30B reasoning chat endpoint.
    Accepts a natural query and returns a response grounded in synthetic demo records.
    Optionally pre-synthesizes audio with Timbre.
    """
    try:
        available_lands = land_service.get_all()
        history_dicts = [{"role": m.role, "content": m.content} for m in req.conversation_history]
        language = detect_conversation_language(req.query, req.language)

        reasoning_res = await evon_service.reason(
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
            ai_mode=reasoning_res.get("ai_mode", "MOCK AI")
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
    Mandatory Prisma v2.5 Speech-to-Text endpoint.
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
    Mandatory Timbre v2.5 Text-to-Speech endpoint.
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
