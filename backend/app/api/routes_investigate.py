import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.ai import (
    CollaborativeInvestigationRequest,
    CollaborativeInvestigationResponse,
    AIModelsHealthResponse
)
from app.services.evon_service import evon_service
from app.services.timbre_service import timbre_service
from app.services.prisma_service import prisma_service
from app.services.land_service import land_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/investigate", tags=["Investigation Universe"])

class ProviderSwitchRequest(BaseModel):
    provider: str # 'GNANI_EVON' | 'QWEN3_OLLAMA' | 'MOCK_DEV_ADAPTER'

@router.post("/collaborate", response_model=CollaborativeInvestigationResponse)
async def collaborate_investigation(req: CollaborativeInvestigationRequest):
    """
    Coordinates the 4 animated AI characters (Bhoomi, Infra, Nyaya, Amma)
    to investigate a land property and generate sequential spoken dialogue with Timbre audio.
    """
    try:
        available_lands = land_service.get_all()

        collab = await evon_service.investigate_collaborative(
            query=req.query,
            conversation_language=req.conversation_language,
            available_lands=available_lands,
            selected_land_id=req.selected_land_id
        )

        # Pre-synthesize Timbre audio for each character in the sequence
        dialogue_items = collab.get("dialogue_sequence", [])
        for item in dialogue_items:
            try:
                char_key = item.get("character", "bhoomi")
                b64, _, dur, voice_used, _ = await timbre_service.speak(
                    text=item.get("text", ""),
                    language=req.conversation_language,
                    character=char_key,
                    voice=item.get("voice_id")
                )
                item["audio_base64"] = b64
                item["duration_sec"] = dur
                item["voice_id"] = voice_used
            except Exception as e:
                logger.warning(f"Audio synthesis warning for {item.get('character')}: {e}")

        return CollaborativeInvestigationResponse(
            user_query=collab.get("user_query", req.query),
            conversation_language=collab.get("conversation_language", req.conversation_language),
            matched_land_ids=collab.get("matched_land_ids", []),
            dialogue_sequence=dialogue_items,
            model_used=collab.get("model_used", "bhoomivaani-dev-adapter"),
            provider=collab.get("provider", "MOCK_DEV_ADAPTER"),
            is_live=collab.get("is_live", False),
            overall_risk_level=collab.get("overall_risk_level", "MODERATE")
        )
    except Exception as e:
        logger.exception(f"Collaborative investigation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")

@router.get("/models/status", response_model=AIModelsHealthResponse)
async def get_models_health():
    """
    Model status endpoint reporting connection status, provider, and live/mock state
    for Prisma v2.5, Evon/Qwen3, and Timbre v2.5.
    """
    prisma_stat = await prisma_service.check_health()
    reasoning_stat = await evon_service.check_health()
    timbre_stat = await timbre_service.check_health()

    all_live = prisma_stat.is_live and reasoning_stat.is_live and timbre_stat.is_live

    return AIModelsHealthResponse(
        active_reasoning_provider=evon_service.provider,
        prisma_stt=prisma_stat,
        reasoning=reasoning_stat,
        timbre_tts=timbre_stat,
        all_live=all_live,
        mock_mode=settings.mock_mode
    )

@router.post("/provider")
async def switch_reasoning_provider(req: ProviderSwitchRequest):
    """
    Switches active reasoning model provider between GNANI_EVON, QWEN3_OLLAMA, and MOCK_DEV_ADAPTER.
    """
    valid = ["GNANI_EVON", "QWEN3_OLLAMA", "MOCK_DEV_ADAPTER"]
    if req.provider not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid provider. Choose from {valid}")

    evon_service.provider = req.provider
    settings.reasoning_provider = req.provider
    logger.info(f"Switched reasoning provider to {req.provider}")

    return {
        "status": "success",
        "new_provider": req.provider,
        "model_info": await evon_service.get_active_model_info()
    }
