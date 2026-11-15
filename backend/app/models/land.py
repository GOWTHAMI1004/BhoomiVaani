from datetime import date
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class ProvenanceClass(str, Enum):
    USER_PROVIDED = "USER_PROVIDED"
    BROKER_PROVIDED = "BROKER_PROVIDED"
    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"
    OFFICIALLY_VERIFIED = "OFFICIALLY_VERIFIED"
    AI_ESTIMATED = "AI_ESTIMATED"
    SYNTHETIC_DEMONSTRATION = "SYNTHETIC_DEMONSTRATION"
    UNKNOWN = "UNKNOWN"


class DataProvenance(BaseModel):
    classification: ProvenanceClass = ProvenanceClass.UNKNOWN
    source_label: str = "Source not recorded"
    source_url: Optional[str] = None
    last_updated: Optional[date] = None
    evidence_references: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def verified_records_require_evidence(self):
        if self.classification == ProvenanceClass.OFFICIALLY_VERIFIED and not (
            self.source_url or self.evidence_references
        ):
            raise ValueError("Officially verified data must include a source URL or evidence reference.")
        return self

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
    record_provenance: DataProvenance = Field(default_factory=DataProvenance)
    field_provenance: Dict[str, DataProvenance] = Field(default_factory=dict)

    @model_validator(mode="after")
    def provide_provenance_for_each_field(self):
        """Every value gets field provenance, inheriting the record source unless overridden."""
        provenance = dict(self.field_provenance)
        for field_name in type(self).model_fields:
            if field_name in {"record_provenance", "field_provenance"}:
                continue
            provenance.setdefault(field_name, self.record_provenance.model_copy(deep=True))
        self.field_provenance = provenance
        return self

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
