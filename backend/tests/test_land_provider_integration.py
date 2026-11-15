from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models.land import Coordinates, DataProvenance, LandListing, ProvenanceClass
from app.models.land_provider import (
    LandSearchSource,
    ListingSubmission,
    ProviderAvailability,
    SubmissionClassification,
    VerificationStatus,
)
from app.services.land_providers import LandProviderRegistry, UserSubmittedListingProvider
from app.services.land_service import land_service


def make_registry(tmp_path, **config_updates):
    config = settings.model_copy(update={
        "land_listing_provider": "USER_SUBMITTED",
        "user_submitted_listings_enabled": True,
        "user_submitted_lands_file": tmp_path / "user-listings.json",
        "land_record_provider": "",
        "land_record_api_key": "",
        "land_geocoding_provider": "",
        "land_geocoding_api_key": "",
        "land_nearby_places_provider": "",
        "land_nearby_places_api_key": "",
        "land_use_provider": "",
        "land_use_api_key": "",
        **config_updates,
    })
    adapter = UserSubmittedListingProvider(
        config.user_submitted_lands_file,
        enabled=config.user_submitted_listings_enabled,
    )
    return LandProviderRegistry(config, listing_provider=adapter)


def make_test_listing():
    return LandListing(
        id="test-submission-1",
        title="Provider test fixture",
        location="Test village",
        district="Test district",
        survey_number="TEST-1",
        acres=1.0,
        price_per_acre_lakhs=10.0,
        total_price_lakhs=10.0,
        land_type="Test fixture",
        legal_status="Not verified",
        growth_score=0,
        image_url="",
        description="Test fixture only; not a real property.",
        coordinates=Coordinates(lat=0.0, lng=0.0),
        record_provenance=DataProvenance(classification=ProvenanceClass.UNKNOWN),
    )


def test_unconfigured_external_providers_report_not_configured_and_no_credentials(tmp_path):
    status = make_registry(tmp_path).get_status(demo_record_count=6)
    for name in ("land_record", "geocoding", "nearby_places", "land_use"):
        provider = status.providers[name]
        assert provider.availability == ProviderAvailability.NOT_CONFIGURED
        assert provider.credentials_configured is False
    assert status.providers["listing"].availability == ProviderAvailability.CONFIGURED_AVAILABLE
    assert status.providers["demonstration_data"].availability == ProviderAvailability.DEMONSTRATION_DATA_ONLY


def test_selected_external_provider_without_key_is_configured_but_unavailable(tmp_path):
    status = make_registry(
        tmp_path,
        land_record_provider="UNSELECTED_ADAPTER",
        land_record_api_key="",
    ).get_status(demo_record_count=6)
    record_provider = status.providers["land_record"]
    assert record_provider.availability == ProviderAvailability.CONFIGURED_UNAVAILABLE
    assert record_provider.credentials_configured is False
    assert "no reviewed adapter" in record_provider.message


def test_provider_status_endpoint_reports_independent_states_without_secret_values(tmp_path, monkeypatch):
    registry = make_registry(
        tmp_path,
        land_record_provider="UNSELECTED_ADAPTER",
        land_record_api_key="test-secret-marker",
    )
    monkeypatch.setattr(land_service, "provider_registry", registry)
    response = TestClient(app).get("/api/lands/providers/status")
    assert response.status_code == 200
    body = response.json()
    assert set(body["providers"]) == {
        "listing", "land_record", "geocoding", "nearby_places", "land_use", "demonstration_data"
    }
    assert body["providers"]["listing"]["availability"] == "CONFIGURED_AVAILABLE"
    assert body["providers"]["land_record"]["availability"] == "CONFIGURED_UNAVAILABLE"
    assert body["providers"]["land_record"]["credentials_configured"] is True
    assert "test-secret-marker" not in response.text


def test_unavailable_listing_provider_returns_503_and_does_not_substitute_demo(tmp_path, monkeypatch):
    registry = make_registry(tmp_path, land_listing_provider="EXTERNAL_NOT_IMPLEMENTED")
    monkeypatch.setattr(land_service, "provider_registry", registry)
    client = TestClient(app)

    response = client.get("/api/lands?source=live")
    assert response.status_code == 503
    assert response.json()["detail"] == "The selected listing provider has no installed adapter."


def test_demo_and_live_search_are_isolated_and_submission_provenance_is_preserved(tmp_path, monkeypatch):
    registry = make_registry(tmp_path)
    monkeypatch.setattr(land_service, "provider_registry", registry)
    client = TestClient(app)
    empty_live = client.get("/api/lands?source=live")
    assert empty_live.status_code == 200
    assert empty_live.json() == []

    submission = ListingSubmission(
        listing=make_test_listing(),
        submitted_as=SubmissionClassification.BROKER_PROVIDED,
        source_url="https://broker.example/listing/123",
    )
    response = client.post("/api/lands/submissions", json=submission.model_dump(mode="json"))
    assert response.status_code == 201
    created = response.json()
    assert created["provenance_classification"] == ProvenanceClass.BROKER_PROVIDED.value
    assert created["verification_status"] == VerificationStatus.NOT_VERIFIED.value
    assert created["provider_record_id"].startswith("user-")
    assert created["data"]["record_provenance"]["classification"] == "BROKER_PROVIDED"
    assert all(
        value["classification"] == "BROKER_PROVIDED"
        for key, value in created["data"]["field_provenance"].items()
        if key != "id"
    )
    assert created["attribution_requirements"]
    assert created["permitted_usage"]["retention_permission"] == "ALLOWED"

    live_response = client.get("/api/lands?source=live")
    assert live_response.status_code == 200
    assert len(live_response.json()) == 1
    assert live_response.json()[0]["record_provenance"]["classification"] == "BROKER_PROVIDED"

    demo_response = client.get("/api/lands?source=demo")
    assert demo_response.status_code == 200
    assert len(demo_response.json()) == 6
    assert all(item["id"].startswith("bv-hyd-") for item in demo_response.json())

    normalized = client.get("/api/lands/provider-search?source=live").json()[0]
    for field in (
        "provider_name", "provider_record_id", "source_url", "retrieval_timestamp",
        "provenance_classification", "verification_status", "coordinate_precision",
        "attribution_requirements", "permitted_usage",
    ):
        assert field in normalized


def test_synthetic_demo_record_cannot_be_submitted_as_live(tmp_path):
    demo_listing = land_service.get_all(source=LandSearchSource.DEMO)[0]
    try:
        ListingSubmission(listing=demo_listing)
    except ValueError as exc:
        assert "Synthetic demonstration records cannot be submitted" in str(exc)
    else:
        raise AssertionError("Synthetic demo listing was accepted as a live submission")


def test_disabled_submission_adapter_reports_unavailable(tmp_path):
    registry = make_registry(tmp_path, user_submitted_listings_enabled=False)
    assert registry.get_status(6).providers["listing"].availability == ProviderAvailability.CONFIGURED_UNAVAILABLE
