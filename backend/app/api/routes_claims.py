from fastapi import APIRouter
from app.models.claim import ClaimCheckRequest, ClaimCheckResponse
from app.services.claim_service import claim_service

router = APIRouter(prefix="/api/claims", tags=["Claims"])

@router.post("/check", response_model=ClaimCheckResponse)
def check_broker_claim(req: ClaimCheckRequest):
    """
    Checks real estate broker statements against verified infrastructure evidence.
    """
    return claim_service.check_claim(req)
