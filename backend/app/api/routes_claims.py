from fastapi import APIRouter, HTTPException
from app.models.claim import ClaimCheckRequest, ClaimCheckResponse
from app.services.claim_service import claim_service

router = APIRouter(prefix="/api/claims", tags=["Claims"])

@router.post("/check", response_model=ClaimCheckResponse)
def check_broker_claim(req: ClaimCheckRequest):
    """
    Compares a claim only with synthetic demonstration entries; it does not verify external records.
    """
    try:
        return claim_service.check_claim(req)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
