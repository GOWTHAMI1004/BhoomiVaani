import logging

from app.models.claim import ClaimCheckRequest, ClaimCheckResponse
from app.services.land_service import land_service

logger = logging.getLogger(__name__)


class ClaimService:
    """Compares a broker statement only with the app's synthetic demonstration records."""

    def check_claim(self, req: ClaimCheckRequest) -> ClaimCheckResponse:
        selected_land = land_service.get_by_id(req.land_id) if req.land_id else None
        if req.land_id and selected_land is None:
            raise ValueError(f"Unknown synthetic demonstration parcel: {req.land_id}")
        statement = req.statement.lower()
        if selected_land:
            lands = [selected_land]
        else:
            lands = land_service.get_all()

        terms = [
            term for term in ("metro", "rrr", "ring road", "highway", "road", "airport", "it park", "sez")
            if term in statement
        ]
        related = [
            item
            for land in lands
            for item in land.infrastructure_evidence
            if any(term in item.claim.lower() for term in terms)
        ]
        if any(term in statement for term in ("guarantee", "guaranteed", "double", "triple", "risk free")):
            matched_claim = "Guaranteed investment return claim"
        elif related:
            matched_claim = related[0].claim
        else:
            matched_claim = None

        record_summary = "; ".join(
            f"{item.claim}: {item.status}, {item.distance_km:g} km"
            for item in related
        )
        available_evidence = (
            f"Synthetic demo listing only: {record_summary}"
            if record_summary
            else "No matching evidence in the synthetic demo listings."
        )
        return ClaimCheckResponse(
            statement=req.statement,
            land_id=req.land_id,
            verification_status="UNVERIFIED",
            confidence_level="Low",
            matched_claim=matched_claim,
            available_evidence=available_evidence,
            explanation=(
                "BhoomiVaani did not query government portals or verify external records. "
                "Any matching status above is copied from synthetic demonstration data and is not evidence that a real project exists."
            ),
            missing_information=(
                "An authoritative, current government order, gazette notification, project record, or parcel-specific map "
                "has not been supplied or independently checked."
            ),
            caution_note=(
                "Treat this claim as unverified. Ask for the exact official record and have it checked with the issuing authority "
                "before relying on it or paying a premium."
            ),
            evidence_type="SYNTHETIC_DEMONSTRATION_DATA",
            ai_mode="RULE_BASED_DEMO",
        )


claim_service = ClaimService()
