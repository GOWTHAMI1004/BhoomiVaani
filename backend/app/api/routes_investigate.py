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
from app.services.reasoning_service import reasoning_service
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

        collab = await reasoning_service.investigate_collaborative(
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

        # The frontend requests speech after this response so it can show the generating state.
        dialogue_items = collab.get("dialogue_sequence", [])

        return CollaborativeInvestigationResponse(
            user_query=collab.get("user_query", req.query),
            conversation_language=collab.get("conversation_language", language),
            matched_land_ids=collab.get("matched_land_ids", []),
            dialogue_sequence=dialogue_items,
            model_used=collab.get("model_used", "UNCONFIGURED"),
            provider=collab.get("provider", "UNCONFIGURED"),
            is_live=collab.get("is_live", False),
            overall_risk_level=collab.get("overall_risk_level", "NOT_ASSESSED"),
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

    report = reasoning_service.build_case_report(
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
    Model status endpoint for Prisma v3.0, the external reasoning adapter, and Timbre v2.5.
    """
    prisma_stat = await prisma_service.check_health()
    reasoning_stat = await reasoning_service.check_health()
    timbre_stat = await timbre_service.check_health()

    available_languages = reasoning_stat.supported_languages

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
    Records a provider selection without assuming its endpoint or request format.
    """
    provider = req.provider.strip()
    if not provider:
        raise HTTPException(
            status_code=422,
            detail="A reasoning provider name is required.",
        )
    reasoning_service.provider = provider
    settings.reasoning_provider = provider
    logger.info("Selected an external reasoning provider adapter: %s", provider)

    return {
        "status": "success",
        "new_provider": provider,
        "model_info": await reasoning_service.get_active_model_info()
    }
