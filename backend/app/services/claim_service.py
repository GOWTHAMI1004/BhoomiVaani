import logging
from typing import Optional, List
from app.models.claim import ClaimCheckRequest, ClaimCheckResponse
from app.services.land_service import land_service

logger = logging.getLogger(__name__)

class ClaimService:
    """
    Evaluates real estate broker claims against synthetic verified public records,
    infrastructure plans, and statutory notifications.
    """

    def check_claim(self, req: ClaimCheckRequest) -> ClaimCheckResponse:
        statement_lower = req.statement.lower()
        selected_land = land_service.get_by_id(req.land_id) if req.land_id else None

        # Gather infrastructure evidence points from specified land or all lands
        evidence_pool = []
        if selected_land:
            for ev in selected_land.infrastructure_evidence:
                evidence_pool.append((selected_land, ev))
        else:
            for l in land_service.get_all():
                for ev in l.infrastructure_evidence:
                    evidence_pool.append((l, ev))

        # Check for Metro Rail claims
        if "metro" in statement_lower:
            # Check if claim says metro will be built in Chevella, Keesara, or Shadnagar
            is_near_term = any(w in statement_lower for w in ["next year", "1 year", "2 year", "soon", "18 months", "months"])
            is_chevella = "chevella" in statement_lower or (selected_land and "chevella" in selected_land.location.lower())
            is_keesara = "keesara" in statement_lower or (selected_land and "keesara" in selected_land.location.lower())

            if is_chevella or is_keesara or "2 km" in statement_lower:
                return ClaimCheckResponse(
                    statement=req.statement,
                    land_id=req.land_id,
                    verification_status="UNVERIFIED",
                    confidence_level="High",
                    matched_claim="Direct Metro Rail Extension to Peri-Urban Tract",
                    available_evidence="Hyderabad Metro Rail Limited (HMRL) Master Plan Phase 2/3 Detail Project Reports (DPR).",
                    explanation=(
                        "HMRL official corridor studies only extend to the Outer Ring Road (Airport, Shamshabad, BHEL-Patancheru). "
                        "There is NO approved DPR, budget allocation, or land survey for extending Metro Rail to Chevella or Keesara. "
                        "The nearest operational metro terminal is over 25 km away."
                    ),
                    missing_information="Government gazette notification, HMRL detailed project report (DPR), and state cabinet financial approval.",
                    caution_note=(
                        "Brokers often conflate generic long-range visionary discussions with approved infrastructure. "
                        "While a project can be discussed in public forums, it remains UNVERIFIED until official DPR and fund sanction are issued."
                    )
                )

        # Check for Regional Ring Road (RRR) claims
        if "rrr" in statement_lower or "regional ring road" in statement_lower or "ring road" in statement_lower:
            return ClaimCheckResponse(
                statement=req.statement,
                land_id=req.land_id,
                verification_status="OFFICIALLY ANNOUNCED / VERIFIED",
                confidence_level="High",
                matched_claim="Regional Ring Road (RRR) Alignment",
                available_evidence="MoRTH Gazette Notification S.O. 2341(E) & Telangana State R&B alignment map.",
                explanation=(
                    "The Regional Ring Road (RRR) project has received central government in-principle approval and gazette notification. "
                    "The Northern and Southern arcs pass through outer zones of Ranga Reddy, Medak, and Yadadri districts."
                ),
                missing_information="Final award inquiry under Section 3-G for individual survey parcel demarcation.",
                caution_note="Always verify whether the specific survey number falls directly inside the acquisition corridor (which would lead to compulsory acquisition) or in the buffer influence zone."
            )

        # Check for Guaranteed Double Returns / 100% Price Jump claims
        if any(w in statement_lower for w in ["double", "guarantee", "guaranteed", "100%", "triple", "18 months", "risk free"]):
            return ClaimCheckResponse(
                statement=req.statement,
                land_id=req.land_id,
                verification_status="CONTRADICTED",
                confidence_level="High",
                matched_claim="Guaranteed Investment Appreciation",
                available_evidence="RERA Regulations and Indian Contract Act precedent regarding financial returns.",
                explanation=(
                    "Real estate market value is subject to macroeconomic fluctuations, land zoning policies, and liquidity. "
                    "Any representation of 'guaranteed doubling' or 'guaranteed returns' is contradicted by statutory real estate disclosures."
                ),
                missing_information="No legally binding escrow guarantee or statutory approval exists for price doubling.",
                caution_note="Never commit funds based on verbal or promotional promises of guaranteed appreciation."
            )

        # Check for Highway Expansion (NH-44 / Chevella-Vikarabad)
        if "highway" in statement_lower or "4-lane" in statement_lower or "6-lane" in statement_lower or "nh-44" in statement_lower:
            return ClaimCheckResponse(
                statement=req.statement,
                land_id=req.land_id,
                verification_status="VERIFIED",
                confidence_level="High",
                matched_claim="Highway Widening Corridor",
                available_evidence="National Highways Authority of India (NHAI) completed project records and state R&B civil contracts.",
                explanation="NH-44 expansion to 6 lanes at Shadnagar is already operational, and Chevella-Vikarabad corridor widening is actively under construction.",
                missing_information="Exact road widening setback line relative to the cadastral survey boundary.",
                caution_note="Confirm physical road boundary stone to prevent buying land located within future road widening right-of-way."
            )

        # Check for IT Park / SEZ claims
        if "it park" in statement_lower or "sez" in statement_lower or "tech city" in statement_lower or "airport" in statement_lower:
            return ClaimCheckResponse(
                statement=req.statement,
                land_id=req.land_id,
                verification_status="UNVERIFIED",
                confidence_level="Medium",
                matched_claim="Greenfield IT Park / Industrial SEZ",
                available_evidence="TSIIC (Telangana State Industrial Infrastructure Corporation) layout archives.",
                explanation=(
                    "No statutory master plan amendment or TSIIC land acquisition order designates this parcel for IT SEZ development. "
                    "Commercial or industrial development claims without TSIIC notification are considered speculative marketing claims."
                ),
                missing_information="TSIIC layout sanction, environmental clearance, and Department of Commerce SEZ notification.",
                caution_note="Do not pay commercial land valuation premiums for unnotified, speculative claims."
            )

        # Default fallback analysis
        return ClaimCheckResponse(
            statement=req.statement,
            land_id=req.land_id,
            verification_status="PROPOSED",
            confidence_level="Medium",
            matched_claim="General Infrastructure Development Claim",
            available_evidence="Regional Master Plan 2031 Vision Document.",
            explanation=(
                "The statement corresponds to broad regional planning aspirations, but specific field-level implementation "
                "depends on statutory budget allocations and tender awards."
            ),
            missing_information="Tender document reference, municipal work order number, and designated survey corridor.",
            caution_note="Ask the broker for the exact government GO (Government Order) or gazette notification reference number before relying on the claim."
        )

claim_service = ClaimService()
