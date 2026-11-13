from typing import List, Optional
from pydantic import BaseModel, Field

class ClaimCheckRequest(BaseModel):
    statement: str
    land_id: Optional[str] = None
    language: str = "te"

class ClaimCheckResponse(BaseModel):
    statement: str
    land_id: Optional[str] = None
    verification_status: str # 'VERIFIED', 'PROPOSED', 'UNVERIFIED', 'CONTRADICTED'
    confidence_level: str # 'High', 'Medium', 'Low'
    matched_claim: Optional[str] = None
    available_evidence: str
    explanation: str
    missing_information: str
    caution_note: str
    ai_mode: str = "MOCK AI"
