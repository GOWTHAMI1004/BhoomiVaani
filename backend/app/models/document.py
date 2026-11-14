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
    overall_risk_score: int # Rule-based text-pattern score, not a property risk rating.
    risk_level: str # Pattern indicator: 'LOW', 'MODERATE', 'HIGH', or 'CRITICAL'.
    detected_issues: List[DetectedIssue] = Field(default_factory=list)
    summary: str
    survey_numbers_found: List[str] = Field(default_factory=list)
    encumbrance_clauses_found: bool = False
    disclaimer: str = (
        "RULE-BASED TEXT SCAN ONLY - NOT LEGAL ADVICE OR TITLE CERTIFICATION. "
        "Extracted statements are user-provided and have not been independently verified. "
        "Consult a qualified property advocate and verify original records with the relevant authorities."
    )
    evidence_type: str = "USER_PROVIDED_DOCUMENT_TEXT"
    ai_mode: str = "RULE_BASED_DOCUMENT_SCAN"
