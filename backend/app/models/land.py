from typing import List, Optional
from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    lat: float
    lng: float

class LegalRiskItem(BaseModel):
    risk_type: str
    severity: str # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    description: str
    recommended_action: str

class InfrastructureEvidence(BaseModel):
    claim: str
    status: str # 'Officially announced', 'Proposed', 'Under construction', 'Operational', 'Unverified claim'
    evidence_source: str
    distance_km: float
    confidence: str # 'High', 'Medium', 'Low'

class LandListing(BaseModel):
    id: str
    title: str
    location: str
    district: str
    survey_number: str
    acres: float
    price_per_acre_lakhs: float
    total_price_lakhs: float
    land_type: str
    legal_status: str
    legal_risks: List[LegalRiskItem] = Field(default_factory=list)
    upcoming_projects: List[str] = Field(default_factory=list)
    infrastructure_evidence: List[InfrastructureEvidence] = Field(default_factory=list)
    growth_score: int
    image_url: str
    description: str
    coordinates: Coordinates

class LandFilterParams(BaseModel):
    district: Optional[str] = None
    min_acres: Optional[float] = None
    max_acres: Optional[float] = None
    max_budget_lakhs: Optional[float] = None
    land_type: Optional[str] = None
    legal_status: Optional[str] = None
    search: Optional[str] = None

class LandComparisonRequest(BaseModel):
    land_ids: List[str]
