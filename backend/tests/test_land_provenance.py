import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import LANDS_FILE
from app.main import app
from app.models.land import DataProvenance, LandListing, ProvenanceClass
from app.services.land_service import land_service

client = TestClient(app)


def test_all_current_demo_records_and_each_field_are_marked_synthetic():
    lands = land_service.get_all()
    assert len(lands) == 6
    for land in lands:
        assert land.record_provenance.classification == ProvenanceClass.SYNTHETIC_DEMONSTRATION
        assert land.record_provenance.last_updated is None
        for name in type(land).model_fields:
            if name in {"record_provenance", "field_provenance"}:
                continue
            assert land.field_provenance[name].classification == ProvenanceClass.SYNTHETIC_DEMONSTRATION
            assert land.field_provenance[name].source_label == "BhoomiVaani synthetic demonstration dataset"


def test_land_api_returns_machine_readable_provenance_for_price_and_coordinates():
    response = client.get("/api/lands")
    assert response.status_code == 200
    first = response.json()[0]
    assert first["record_provenance"]["classification"] == "SYNTHETIC_DEMONSTRATION"
    assert first["record_provenance"]["last_updated"] is None
    assert first["field_provenance"]["price_per_acre_lakhs"]["classification"] == "SYNTHETIC_DEMONSTRATION"
    assert first["field_provenance"]["coordinates"]["classification"] == "SYNTHETIC_DEMONSTRATION"


def test_land_source_status_is_explicit_about_missing_live_providers():
    response = client.get("/api/lands/source-status")
    assert response.status_code == 200
    assert response.json()["total_records"] == 6
    assert response.json()["records_by_classification"] == {"SYNTHETIC_DEMONSTRATION": 6}
    assert response.json()["real_listing_feed"] == "NOT_CONFIGURED"
    assert response.json()["official_land_records"] == "NOT_CONFIGURED"
    assert response.json()["map_and_poi_provider"] == "NOT_CONFIGURED"


def test_unsourced_future_record_fields_default_to_unknown():
    record = json.loads(Path(LANDS_FILE).read_text(encoding="utf-8"))[0]
    record.pop("field_provenance", None)
    record["record_provenance"] = {"classification": "UNKNOWN", "source_label": "Source not recorded"}
    land = LandListing.model_validate(record)
    assert land.field_provenance["coordinates"].classification == ProvenanceClass.UNKNOWN


def test_official_verification_requires_evidence_reference():
    with pytest.raises(ValueError, match="must include a source URL or evidence reference"):
        DataProvenance(classification="OFFICIALLY_VERIFIED", source_label="Official")
