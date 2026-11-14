import json
import logging
from typing import List, Optional, Dict, Any
from app.config import LANDS_FILE
from app.models.land import LandListing, LandFilterParams

logger = logging.getLogger(__name__)

class LandService:
    def __init__(self):
        self._lands: List[LandListing] = []
        self._load_lands()

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

    def get_all(self, params: Optional[LandFilterParams] = None) -> List[LandListing]:
        results = self._lands.copy()

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

    def get_by_id(self, land_id: str) -> Optional[LandListing]:
        for l in self._lands:
            if l.id == land_id:
                return l
        return None

    def compare(self, land_ids: List[str]) -> List[LandListing]:
        id_set = set(land_ids)
        return [l for l in self._lands if l.id in id_set]

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

land_service = LandService()
