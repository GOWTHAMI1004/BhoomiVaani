import asyncio
import logging
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from app.models.ai import (
    CollaborativeInvestigationRequest,
    CollaborativeInvestigationResponse,
    AIModelsHealthResponse,
    InvestigationReportRequest,
)
from app.services.report_service import report_service
from app.services.evon_service import evon_service
from app.services.timbre_service import timbre_service
from app.services.prisma_service import prisma_service
from app.services.land_service import land_service
from app.services.ai_errors import ProviderRequestError, ProviderUnavailableError
from app.config import settings
from app.services.language_service import detect_conversation_language

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/investigate", tags=["Investigation Universe"])

class ProviderSwitchRequest(BaseModel):
    provider: str

@router.post("/collaborate", response_model=CollaborativeInvestigationResponse)
async def collaborate_investigation(req: CollaborativeInvestigationRequest):
    """
    Uses the configured reasoning provider and adds Timbre audio to Bhoomi's response.
    """
    try:
        language = detect_conversation_language(req.query, req.conversation_language)
        available_lands = land_service.get_all()
        if req.selected_land_id and not any(land.id == req.selected_land_id for land in available_lands):
            raise HTTPException(status_code=404, detail="Selected demonstration parcel was not found.")

        collab = await evon_service.investigate_collaborative(
            query=req.query,
            conversation_language=language,
            available_lands=available_lands,
            selected_land_id=req.selected_land_id,
            conversation_history=[
                {"role": message.role, "content": message.content}
                for message in req.conversation_history
            ],
            document_analyses=[
                document.model_dump() for document in req.document_analyses
            ],
        )

        # Speech is optional for the text report, but failures remain visible to the client.
        dialogue_items = collab.get("dialogue_sequence", [])

        if dialogue_items:
            item = dialogue_items[-1]
            try:
                b64, _, dur, voice_used, _ = await asyncio.wait_for(
                    timbre_service.speak(
                        text=item.get("text", ""),
                        language=collab.get("conversation_language", language),
                        character="bhoomi"
                    ),
                    timeout=min(settings.api_timeout_seconds, 20.0),
                )
                item["audio_base64"] = b64
                item["duration_sec"] = dur
                item["voice_id"] = voice_used
            except (ProviderRequestError, ProviderUnavailableError) as exc:
                logger.warning("Bhoomi narration unavailable: %s", exc)
                item["audio_error"] = str(exc)
            except TimeoutError:
                item["audio_error"] = "Timbre speech request timed out; the text investigation is still available."
                logger.warning("Bhoomi narration timed out")

        return CollaborativeInvestigationResponse(
            user_query=collab.get("user_query", req.query),
            conversation_language=collab.get("conversation_language", language),
            matched_land_ids=collab.get("matched_land_ids", []),
            dialogue_sequence=dialogue_items,
            model_used=collab.get("model_used", "bhoomivaani-dev-adapter"),
            provider=collab.get("provider", "GNANI_EVON"),
            is_live=collab.get("is_live", False),
            overall_risk_level=collab.get("overall_risk_level", "MODERATE"),
            investigation_report=collab.get("investigation_report")
        )
    except HTTPException:
        raise
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ProviderRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as e:
        logger.exception(f"Collaborative investigation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Investigation request failed.")


@router.post("/report")
def download_investigation_report(req: InvestigationReportRequest):
    history = [
        {"role": message.role, "content": message.content}
        for message in req.conversation_history
    ]
    if not any(message["role"] == "user" for message in history):
        raise HTTPException(status_code=400, detail="A buyer conversation is required to generate a report.")

    land = None
    if req.selected_land_id:
        land = land_service.get_by_id(req.selected_land_id)
        if land is None:
            raise HTTPException(status_code=404, detail="Selected demonstration parcel was not found.")

    report = evon_service.build_case_report(
        history,
        land,
        [document.model_dump() for document in req.document_analyses],
    )
    pdf_bytes = report_service.generate_case_report(report)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="BhoomiVaani_Land_Buying_Report.pdf"'},
    )

@router.get("/models/status", response_model=AIModelsHealthResponse)
async def get_models_health():
    """
    Model status endpoint reporting connection status, provider, and live/mock state
    for Prisma v2.5, Evon/Qwen3, and Timbre v2.5.
    """
    prisma_stat = await prisma_service.check_health()
    reasoning_stat = await evon_service.check_health()
    timbre_stat = await timbre_service.check_health()

    available_languages = (
        ["te", "hi", "en"]
        if settings.mock_mode
        else reasoning_stat.supported_languages
    )

    return AIModelsHealthResponse(
        active_reasoning_provider=reasoning_stat.provider,
        prisma_stt=prisma_stat,
        reasoning=reasoning_stat,
        timbre_tts=timbre_stat,
        all_live=prisma_stat.is_live and reasoning_stat.is_live and timbre_stat.is_live,
        mock_mode=settings.mock_mode,
        available_conversation_languages=available_languages
    )

@router.post("/provider")
async def switch_reasoning_provider(req: ProviderSwitchRequest):
    """
    Allows selecting the documented Evon integration only; there are no fallback providers.
    """
    if req.provider != "GNANI_EVON":
        raise HTTPException(
            status_code=400,
            detail="Only GNANI_EVON is supported. Ollama and synthetic reasoning are not available.",
        )

    evon_service.provider = req.provider
    settings.reasoning_provider = req.provider
    logger.info(f"Switched reasoning provider to {req.provider}")

    return {
        "status": "success",
        "new_provider": req.provider,
        "model_info": await evon_service.get_active_model_info()
    }
