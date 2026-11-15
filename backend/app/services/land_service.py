import json
import logging
from typing import List, Optional, Dict, Any
from app.config import LANDS_FILE
from app.models.land import LandListing, LandFilterParams
from app.models.land_provider import (
    CoordinatePrecision,
    LandProvidersStatus,
    LandSearchSource,
    ListingSubmission,
    NormalizedProviderRecord,
    PermissionStatus,
    ProviderUsageMetadata,
    VerificationStatus,
)
from app.services.land_providers import LandProviderRegistry

logger = logging.getLogger(__name__)

class LandService:
    def __init__(self, provider_registry: Optional[LandProviderRegistry] = None):
        self._lands: List[LandListing] = []
        self._load_lands()
        self.provider_registry = provider_registry or LandProviderRegistry()

    def _load_lands(self):
        try:
            with open(LANDS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list) or not data:
                    raise ValueError("land dataset must be a non-empty JSON list")
                self._lands = [LandListing(**item) for item in data]
                logger.info(f"Loaded {len(self._lands)} synthetic land listings from {LANDS_FILE}")
        except Exception as e:
            logger.exception("Failed to load land dataset from %s", LANDS_FILE)
            raise RuntimeError(f"Unable to load required land dataset: {LANDS_FILE}") from e

    def _filter(self, listings: List[LandListing], params: Optional[LandFilterParams]) -> List[LandListing]:
        results = listings.copy()

        if not params:
            return results

        if params.district:
            d = params.district.lower()
            results = [l for l in results if d in l.district.lower()]

        if params.min_acres is not None:
            results = [l for l in results if l.acres >= params.min_acres]

        if params.max_acres is not None:
            results = [l for l in results if l.acres <= params.max_acres]

        if params.max_budget_lakhs is not None:
            results = [l for l in results if l.total_price_lakhs <= params.max_budget_lakhs]

        if params.land_type:
            lt = params.land_type.lower()
            results = [l for l in results if lt in l.land_type.lower()]

        if params.legal_status:
            ls = params.legal_status.lower()
            results = [l for l in results if ls in l.legal_status.lower()]

        if params.search:
            s = params.search.lower()
            results = [
                l for l in results
                if s in l.title.lower()
                or s in l.location.lower()
                or s in l.district.lower()
                or s in l.survey_number.lower()
                or s in l.description.lower()
            ]

        return results

    def get_all(
        self,
        params: Optional[LandFilterParams] = None,
        source: LandSearchSource = LandSearchSource.DEMO,
    ) -> List[LandListing]:
        if source == LandSearchSource.DEMO:
            return self._filter(self._lands, params)
        records = self.provider_registry.search_listings(source, params)
        return [LandListing.model_validate(record.data) for record in records]

    def get_provider_records(
        self,
        source: LandSearchSource = LandSearchSource.DEMO,
        params: Optional[LandFilterParams] = None,
    ) -> List[NormalizedProviderRecord]:
        if source == LandSearchSource.LIVE:
            return self.provider_registry.search_listings(source, params)
        listings = self._filter(self._lands, params)
        results = []
        for listing in listings:
            provenance = listing.record_provenance
            results.append(NormalizedProviderRecord(
                provider_name="local_synthetic_dataset",
                provider_record_id=listing.id,
                data=listing.model_dump(mode="json"),
                source_url=provenance.source_url,
                provenance_classification=provenance.classification,
                verification_status=VerificationStatus.NOT_VERIFIED,
                coordinate_precision=CoordinatePrecision.UNKNOWN,
                attribution_requirements=["Clearly label as synthetic demonstration data."],
                permitted_usage=ProviderUsageMetadata(
                    display_permission=PermissionStatus.ALLOWED,
                    retention_permission=PermissionStatus.ALLOWED,
                    terms_reference="BhoomiVaani demonstration dataset",
                ),
            ))
        return results

    def submit_listing(self, submission: ListingSubmission) -> NormalizedProviderRecord:
        return self.provider_registry.submit_listing(submission)

    def get_by_id(self, land_id: str) -> Optional[LandListing]:
        for l in self._lands:
            if l.id == land_id:
                return l
        if land_id.startswith("user-"):
            for record in self.provider_registry.search_listings(LandSearchSource.LIVE):
                listing = LandListing.model_validate(record.data)
                if listing.id == land_id:
                    return listing
        return None

    def compare(self, land_ids: List[str]) -> List[LandListing]:
        id_set = set(land_ids)
        results = [l for l in self._lands if l.id in id_set]
        demo_ids = {listing.id for listing in results}
        if any(land_id.startswith("user-") for land_id in id_set):
            for record in self.provider_registry.search_listings(LandSearchSource.LIVE):
                listing = LandListing.model_validate(record.data)
                if listing.id in id_set and listing.id not in demo_ids:
                    results.append(listing)
        return results

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._lands)
        clean_count = sum(1 for l in self._lands if not l.legal_risks)
        disputed_count = sum(1 for l in self._lands if len(l.legal_risks) > 0 or "disputed" in l.legal_status.lower())
        avg_growth = round(sum(l.growth_score for l in self._lands) / total, 1) if total > 0 else 0

        return {
            "total_properties": total,
            "records_without_listed_risks": clean_count,
            # Kept for older clients; this is not a title or document verification count.
            "clean_document_examples": clean_count,
            "risk_flagged_properties": disputed_count,
            "average_growth_score": avg_growth,
            "districts": list({l.district for l in self._lands}),
            "land_types": list({l.land_type for l in self._lands})
        }

    def get_source_status(self) -> Dict[str, Any]:
        classifications: Dict[str, int] = {}
        for land in self._lands:
            key = land.record_provenance.classification.value
            classifications[key] = classifications.get(key, 0) + 1
        provider_status = self.provider_registry.get_status(len(self._lands))
        listing_status = provider_status.providers["listing"].availability.value
        land_record_status = provider_status.providers["land_record"].availability.value
        map_provider_status = (
            provider_status.providers["geocoding"].availability.value
            if provider_status.providers["geocoding"].availability.value != "NOT_CONFIGURED"
            else provider_status.providers["nearby_places"].availability.value
        )
        return {
            **provider_status.model_dump(mode="json"),
            "total_records": len(self._lands),
            "records_by_classification": classifications,
            "real_listing_feed": (
                "NOT_CONFIGURED"
                if provider_status.providers["listing"].provider_name == "user_submitted_listings"
                else listing_status
            ),
            "official_land_records": land_record_status,
            "map_and_poi_provider": map_provider_status,
            "note": "Demo records are isolated from live submissions. External provider adapters are not implemented.",
        }

land_service = LandService()
