"""Tests for Informal Settlement Encroachment Detection via Dilated FCNs (Persello & Stein, 2017)."""

import pytest

from alveris.ingestion.cadastre import (
    InformalSettlementEncroachmentResult,
    detect_informal_settlement_encroachment,
)
from alveris.ingestion.parcel import load_parcel_from_geojson


@pytest.fixture
def mock_parcel():
    """Load sample coastal parcel asset for testing."""
    return load_parcel_from_geojson("data/sample/coastal_periurban_parcel.geojson")


def test_no_informal_encroachment(mock_parcel):
    """Verify that formal layout with baseline density yields no informal encroachment."""
    res = detect_informal_settlement_encroachment(
        mock_parcel,
        simulated_encroachment_area_m2=0.0,
        building_density_ratio=1.0,
    )

    assert isinstance(res, InformalSettlementEncroachmentResult)
    assert res.has_informal_settlement_encroachment is False
    assert res.informal_settlement_area_m2 == 0.0
    assert res.setback_violation_flag is False
    assert res.recommended_informal_haircut == 0.0
    assert res.dilated_fcn_receptive_field_m == 25


def test_informal_settlement_encroachment_detected(mock_parcel):
    """Verify that high-density informal structures trigger setback violations and valuation haircut."""
    res = detect_informal_settlement_encroachment(
        mock_parcel,
        simulated_encroachment_area_m2=350.0,
        building_density_ratio=1.65,
    )

    assert isinstance(res, InformalSettlementEncroachmentResult)
    assert res.has_informal_settlement_encroachment is True
    assert res.informal_settlement_area_m2 == 350.0
    assert res.setback_violation_flag is True
    assert res.recommended_informal_haircut > 0.0
    assert "dilated_fcn_dk6_spatial_receptive_field" in res.lineage.processing_method
