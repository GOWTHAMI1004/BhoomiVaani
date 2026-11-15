from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.land import Coordinates, DataProvenance, LandListing, ProvenanceClass


class LandSearchSource(str, Enum):
    DEMO = "demo"
    LIVE = "live"


class ProviderAvailability(str, Enum):
    CONFIGURED_AVAILABLE = "CONFIGURED_AVAILABLE"
    CONFIGURED_UNAVAILABLE = "CONFIGURED_UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    DEMONSTRATION_DATA_ONLY = "DEMONSTRATION_DATA_ONLY"


class VerificationStatus(str, Enum):
    NOT_VERIFIED = "NOT_VERIFIED"
    SOURCE_RECORDED = "SOURCE_RECORDED"
    INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class CoordinatePrecision(str, Enum):
    PARCEL = "PARCEL"
    ADDRESS = "ADDRESS"
    LOCALITY = "LOCALITY"
    APPROXIMATE = "APPROXIMATE"
    UNKNOWN = "UNKNOWN"


class PermissionStatus(str, Enum):
    ALLOWED = "ALLOWED"
    REQUIRES_ATTRIBUTION = "REQUIRES_ATTRIBUTION"
    NOT_CONFIRMED = "NOT_CONFIRMED"
    NOT_ALLOWED = "NOT_ALLOWED"


class ProviderUsageMetadata(BaseModel):
    display_permission: PermissionStatus = PermissionStatus.NOT_CONFIRMED
    retention_permission: PermissionStatus = PermissionStatus.NOT_CONFIRMED
    retention_ttl_seconds: Optional[int] = None
    terms_reference: Optional[str] = None

    @model_validator(mode="after")
    def cache_ttl_must_be_positive(self):
        if self.retention_ttl_seconds is not None and self.retention_ttl_seconds <= 0:
            raise ValueError("retention_ttl_seconds must be positive")
        return self


class NormalizedProviderRecord(BaseModel):
    provider_name: str
    provider_record_id: str
    data: Dict[str, Any]
    source_url: Optional[str] = None
    retrieval_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_classification: ProvenanceClass
    verification_status: VerificationStatus = VerificationStatus.NOT_VERIFIED
    coordinate_precision: CoordinatePrecision = CoordinatePrecision.UNKNOWN
    attribution_requirements: List[str] = Field(default_factory=list)
    permitted_usage: ProviderUsageMetadata = Field(default_factory=ProviderUsageMetadata)


class ProviderStatus(BaseModel):
    provider_type: str
    provider_name: Optional[str] = None
    availability: ProviderAvailability
    credentials_configured: bool = False
    message: str


class LandProvidersStatus(BaseModel):
    providers: Dict[str, ProviderStatus]
    demonstration_record_count: int


class SubmissionClassification(str, Enum):
    USER_PROVIDED = "USER_PROVIDED"
    BROKER_PROVIDED = "BROKER_PROVIDED"


class ListingSubmission(BaseModel):
    listing: LandListing
    submitted_as: SubmissionClassification = SubmissionClassification.USER_PROVIDED
    source_url: Optional[str] = None
    coordinate_precision: CoordinatePrecision = CoordinatePrecision.UNKNOWN

    @model_validator(mode="after")
    def refuse_demo_records(self):
        if self.listing.id.startswith("bv-hyd-"):
            raise ValueError("Synthetic demonstration records cannot be submitted as live listings.")
        if self.listing.record_provenance.classification == ProvenanceClass.SYNTHETIC_DEMONSTRATION:
            raise ValueError("Synthetic demonstration records cannot be submitted as live listings.")
        if any(
            item.classification == ProvenanceClass.SYNTHETIC_DEMONSTRATION
            for item in self.listing.field_provenance.values()
        ):
            raise ValueError("Synthetic demonstration records cannot be submitted as live listings.")
        return self


def provenance_for_submission(submission: ListingSubmission) -> DataProvenance:
    label = (
        "User-provided listing"
        if submission.submitted_as == SubmissionClassification.USER_PROVIDED
        else "Broker-provided listing; claim not independently verified"
    )
    return DataProvenance(
        classification=ProvenanceClass(submission.submitted_as.value),
        source_label=label,
        source_url=submission.source_url,
    )


def listing_with_submission_provenance(submission: ListingSubmission, listing_id: str) -> LandListing:
    provenance = provenance_for_submission(submission)
    field_provenance = {
        field_name: provenance.model_copy(deep=True)
        for field_name in type(submission.listing).model_fields
        if field_name not in {"record_provenance", "field_provenance"}
    }
    return submission.listing.model_copy(update={
        "id": listing_id,
        "record_provenance": provenance,
        "field_provenance": field_provenance,
    })


def normalized_submission_record(
    submission: ListingSubmission,
    listing_id: str,
) -> NormalizedProviderRecord:
    listing = listing_with_submission_provenance(submission, listing_id)
    classification = ProvenanceClass(submission.submitted_as.value)
    return NormalizedProviderRecord(
        provider_name="user_submitted_listings",
        provider_record_id=listing_id,
        data=listing.model_dump(mode="json"),
        source_url=submission.source_url,
        provenance_classification=classification,
        verification_status=VerificationStatus.NOT_VERIFIED,
        coordinate_precision=submission.coordinate_precision,
        attribution_requirements=[
            "Label as user-provided or broker-provided; do not imply independent verification."
        ],
        permitted_usage=ProviderUsageMetadata(
            display_permission=PermissionStatus.ALLOWED,
            retention_permission=PermissionStatus.ALLOWED,
            terms_reference="Direct submission to BhoomiVaani",
        ),
    )
