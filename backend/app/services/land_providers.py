import json
import logging
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import List, Optional, Protocol, runtime_checkable
from uuid import uuid4

from app.config import Settings, settings
from app.models.land import Coordinates, LandFilterParams, LandListing, ProvenanceClass
from app.models.land_provider import (
    CoordinatePrecision,
    LandProvidersStatus,
    LandSearchSource,
    ListingSubmission,
    NormalizedProviderRecord,
    ProviderAvailability,
    ProviderStatus,
    VerificationStatus,
    normalized_submission_record,
)

logger = logging.getLogger(__name__)


class ProviderUnavailableError(RuntimeError):
    pass


@runtime_checkable
class ListingProvider(Protocol):
    provider_name: str

    def search(self, params: Optional[LandFilterParams] = None) -> List[NormalizedProviderRecord]: ...
    def submit(self, submission: ListingSubmission) -> NormalizedProviderRecord: ...


@runtime_checkable
class LandRecordProvider(Protocol):
    provider_name: str

    def lookup(self, reference: str) -> List[NormalizedProviderRecord]: ...


@runtime_checkable
class GeocodingProvider(Protocol):
    provider_name: str

    def geocode(self, query: str) -> List[NormalizedProviderRecord]: ...


@runtime_checkable
class NearbyPlacesProvider(Protocol):
    provider_name: str

    def search_nearby(
        self, coordinates: Coordinates, categories: List[str], radius_meters: int
    ) -> List[NormalizedProviderRecord]: ...


@runtime_checkable
class LandUseProvider(Protocol):
    provider_name: str

    def lookup(self, coordinates: Coordinates) -> List[NormalizedProviderRecord]: ...


class UserSubmittedListingProvider:
    """Local JSON adapter for user/broker submissions, separate from demo fixtures."""

    provider_name = "user_submitted_listings"

    def __init__(self, data_file: Path, enabled: bool = True):
        self.data_file = Path(data_file)
        self.enabled = enabled
        self._lock = RLock()

    def _read(self) -> List[NormalizedProviderRecord]:
        if not self.data_file.exists():
            return []
        try:
            payload = json.loads(self.data_file.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError("user-submitted land store must be a JSON list")
            return [NormalizedProviderRecord.model_validate(item) for item in payload]
        except Exception as exc:
            logger.error("Could not load user-submitted listings (%s)", type(exc).__name__)
            raise ProviderUnavailableError("User-submitted listing store is unavailable.") from exc

    def search(self, params: Optional[LandFilterParams] = None) -> List[NormalizedProviderRecord]:
        if not self.enabled:
            raise ProviderUnavailableError("User-submitted listings are disabled by configuration.")
        with self._lock:
            records = self._read()
        if params is None:
            return records
        filtered = []
        for record in records:
            listing = LandListing.model_validate(record.data)
            if params.district and params.district.lower() not in listing.district.lower():
                continue
            if params.min_acres is not None and listing.acres < params.min_acres:
                continue
            if params.max_acres is not None and listing.acres > params.max_acres:
                continue
            if params.max_budget_lakhs is not None and listing.total_price_lakhs > params.max_budget_lakhs:
                continue
            if params.land_type and params.land_type.lower() not in listing.land_type.lower():
                continue
            if params.legal_status and params.legal_status.lower() not in listing.legal_status.lower():
                continue
            if params.search:
                query = params.search.lower()
                if not any(query in value.lower() for value in (
                    listing.title, listing.location, listing.district,
                    listing.survey_number, listing.description,
                )):
                    continue
            filtered.append(record)
        return filtered

    def submit(self, submission: ListingSubmission) -> NormalizedProviderRecord:
        if not self.enabled:
            raise ProviderUnavailableError("User-submitted listings are disabled by configuration.")
        listing_id = f"user-{uuid4().hex}"
        record = normalized_submission_record(submission, listing_id)
        with self._lock:
            current = self._read()
            current.append(record)
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=self.data_file.parent,
                    prefix=f"{self.data_file.name}.", suffix=".tmp", delete=False,
                ) as handle:
                    temporary_path = Path(handle.name)
                    json.dump([item.model_dump(mode="json") for item in current], handle, ensure_ascii=False, indent=2)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_path, self.data_file)
            except OSError as exc:
                if temporary_path:
                    temporary_path.unlink(missing_ok=True)
                logger.error("Could not persist user-submitted listing (%s)", type(exc).__name__)
                raise ProviderUnavailableError("Could not save the listing submission.") from exc
        return record


class LandProviderRegistry:
    def __init__(self, config: Settings = settings, listing_provider: Optional[UserSubmittedListingProvider] = None):
        self.config = config
        self.listing_provider = listing_provider or UserSubmittedListingProvider(
            config.user_submitted_lands_file,
            enabled=config.user_submitted_listings_enabled,
        )

    def _status(self, provider_type: str, provider_name: str, api_key: str) -> ProviderStatus:
        if not provider_name:
            return ProviderStatus(
                provider_type=provider_type,
                availability=ProviderAvailability.NOT_CONFIGURED,
                credentials_configured=bool(api_key),
                message="No provider is selected.",
            )
        if provider_type == "listing" and provider_name.upper() == "USER_SUBMITTED":
            available = self.listing_provider.enabled
            return ProviderStatus(
                provider_type=provider_type,
                provider_name=self.listing_provider.provider_name,
                availability=(ProviderAvailability.CONFIGURED_AVAILABLE if available else ProviderAvailability.CONFIGURED_UNAVAILABLE),
                message=("Local submission adapter is ready." if available else "Local submission adapter is disabled."),
            )
        return ProviderStatus(
            provider_type=provider_type,
            provider_name=provider_name,
            availability=ProviderAvailability.CONFIGURED_UNAVAILABLE,
            credentials_configured=bool(api_key),
            message="Provider is selected, but no reviewed adapter is installed.",
        )

    def get_status(self, demo_record_count: int) -> LandProvidersStatus:
        providers = {
            "listing": self._status("listing", self.config.land_listing_provider, self.config.land_listing_api_key),
            "land_record": self._status("land_record", self.config.land_record_provider, self.config.land_record_api_key),
            "geocoding": self._status("geocoding", self.config.land_geocoding_provider, self.config.land_geocoding_api_key),
            "nearby_places": self._status("nearby_places", self.config.land_nearby_places_provider, self.config.land_nearby_places_api_key),
            "land_use": self._status("land_use", self.config.land_use_provider, self.config.land_use_api_key),
            "demonstration_data": ProviderStatus(
                provider_type="demonstration_data",
                provider_name="local_synthetic_dataset",
                availability=ProviderAvailability.DEMONSTRATION_DATA_ONLY,
                message=f"{demo_record_count} synthetic records are available only in demo source mode.",
            ),
        }
        return LandProvidersStatus(providers=providers, demonstration_record_count=demo_record_count)

    def search_listings(self, source: LandSearchSource, params: Optional[LandFilterParams] = None) -> List[NormalizedProviderRecord]:
        if source == LandSearchSource.DEMO:
            raise ValueError("Demo records are served by LandService, not the live listing provider.")
        if not self.config.land_listing_provider or self.config.land_listing_provider.upper() != "USER_SUBMITTED":
            raise ProviderUnavailableError("The selected listing provider has no installed adapter.")
        return self.listing_provider.search(params)

    def submit_listing(self, submission: ListingSubmission) -> NormalizedProviderRecord:
        if not self.config.land_listing_provider or self.config.land_listing_provider.upper() != "USER_SUBMITTED":
            raise ProviderUnavailableError("User-submitted listings are not the selected listing source.")
        return self.listing_provider.submit(submission)
