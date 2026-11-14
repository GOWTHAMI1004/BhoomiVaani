from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class ClaimCheckRequest(BaseModel):
    statement: str = Field(min_length=1, max_length=2000)
    land_id: Optional[str] = None
    language: str = "te"

    @field_validator("statement")
    @classmethod
    def statement_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Claim statement must contain non-whitespace text.")
        return value

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
    evidence_type: str = "SYNTHETIC_DEMONSTRATION_DATA"
    ai_mode: str = "RULE_BASED_DEMO"
