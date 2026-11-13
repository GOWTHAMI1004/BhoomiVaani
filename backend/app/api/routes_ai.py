import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.models.ai import AIChatRequest, AIChatResponse, SpeakRequest, SpeakResponse
from app.services.prisma_service import prisma_service
from app.services.evon_service import evon_service
from app.services.timbre_service import timbre_service
from app.services.land_service import land_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI"])

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_evon(req: AIChatRequest):
    """
    Mandatory Evon v3.3 30B reasoning chat endpoint.
    Accepts natural query, performs grounding against verified database, returns structured response.
    Optionally pre-synthesizes audio with Timbre.
    """
    try:
        available_lands = land_service.get_all()
        history_dicts = [{"role": m.role, "content": m.content} for m in req.conversation_history]

        reasoning_res = await evon_service.reason(
            query=req.query,
            language=req.language,
            conversation_history=history_dicts,
            available_lands=available_lands,
            selected_land_id=req.selected_land_id
        )

        # Synthesize audio with Timbre v2.5 / mock audio
        audio_b64 = None
        audio_available = False
        try:
            audio_b64, _, _, _, _ = await timbre_service.speak(
                text=reasoning_res["response"],
                language=req.language
            )
            audio_available = bool(audio_b64)
        except Exception as e:
            logger.warning(f"Audio synthesis warning: {str(e)}")

        return AIChatResponse(
            transcript=reasoning_res.get("transcript", req.query),
            response=reasoning_res.get("response", ""),
            language=req.language,
            matched_land_ids=reasoning_res.get("matched_land_ids", []),
            legal_warnings=reasoning_res.get("legal_warnings", []),
            infrastructure_findings=reasoning_res.get("infrastructure_findings", []),
            growth_insights=reasoning_res.get("growth_insights", []),
            audio_base64=audio_b64,
            audio_available=audio_available,
            ai_mode=reasoning_res.get("ai_mode", "MOCK AI")
        )
    except Exception as e:
        logger.exception(f"Chat pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Chat error: {str(e)}")

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("indic-auto")
):
    """
    Mandatory Prisma v2.5 Speech-to-Text endpoint.
    Transcribes uploaded audio bytes.
    """
    try:
        audio_bytes = await file.read()
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file provided.")

        transcript, detected_lang, ai_mode, is_live = await prisma_service.transcribe(
            audio_bytes=audio_bytes,
            filename=file.filename or "recording.wav",
            language_code=language
        )

        return {
            "transcript": transcript,
            "detected_language": detected_lang,
            "ai_mode": ai_mode,
            "is_live": is_live
        }
    except Exception as e:
        logger.exception(f"STT pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@router.post("/speak", response_model=SpeakResponse)
async def text_to_speech(req: SpeakRequest):
    """
    Mandatory Timbre v2.5 Text-to-Speech endpoint.
    """
    try:
        audio_b64, ai_mode, duration, voice_used, is_live = await timbre_service.speak(
            text=req.text,
            language=req.language,
            character=getattr(req, 'character', 'bhoomi'),
            voice=req.voice or "Nalini",
            speed=req.speed
        )

        return SpeakResponse(
            audio_base64=audio_b64,
            format="audio/wav",
            language=req.language,
            character=getattr(req, 'character', 'bhoomi'),
            voice_used=voice_used,
            ai_mode=ai_mode,
            duration_estimate_sec=duration
        )
            ai_mode=ai_mode,
            duration_estimate_sec=duration
        )
    except Exception as e:
        logger.exception(f"TTS pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text-to-speech error: {str(e)}")
