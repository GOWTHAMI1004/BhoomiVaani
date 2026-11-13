from typing import List, Optional
from pydantic import BaseModel, Field

class DetectedIssue(BaseModel):
    issue_title: str
    risk_level: str # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'CLEAR'
    snippet: str
    explanation: str
    lawyer_questions: List[str]

class DocumentAnalysisResponse(BaseModel):
    filename: str
    total_characters: int
    overall_risk_score: int # 0 (Safe) to 100 (Extremely Risky)
    risk_level: str # 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'
    detected_issues: List[DetectedIssue] = Field(default_factory=list)
    summary: str
    survey_numbers_found: List[str] = Field(default_factory=list)
    encumbrance_clauses_found: bool = False
    disclaimer: str = (
        "PRELIMINARY DOCUMENT AWARENESS TOOL ONLY - NOT LEGAL ADVICE OR TITLE CERTIFICATION. "
        "Consult a qualified property advocate and verify original records with the Sub-Registrar and revenue authorities."
    )
    ai_mode: str = "MOCK AI"
