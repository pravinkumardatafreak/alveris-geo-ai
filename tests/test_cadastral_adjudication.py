"""Tests for Cadastral Boundary Adjudication and UN SDG 1.4.2 Compliance."""

import pytest

from alveris.ingestion.cadastre import (
    CadastralAdjudicationResult,
    adjudicate_cadastral_boundaries,
)
from alveris.ingestion.parcel import load_parcel_from_geojson


@pytest.fixture
def mock_parcel():
    """Load sample coastal parcel asset for cadastral testing."""
    return load_parcel_from_geojson("data/sample/coastal_periurban_parcel.geojson")


def test_adjudicate_perfect_alignment(mock_parcel):
    """Verify that 0 displacement produces 100% IoU and 0 title haircut."""
    res = adjudicate_cadastral_boundaries(mock_parcel, simulated_boundary_jitter_m=0.0)

    assert isinstance(res, CadastralAdjudicationResult)
    assert res.boundary_iou == 1.0
    assert res.mean_boundary_displacement_m == 0.0
    assert res.encroachment_detected is False
    assert res.sdg_1_4_2_compliant is True
    assert res.recommended_title_haircut == 0.0
    assert res.cadastral_certainty_score >= 95.0


def test_adjudicate_encroachment_detected(mock_parcel):
    """Verify that large boundary shift flags encroachment and calculates title haircut."""
    res = adjudicate_cadastral_boundaries(mock_parcel, simulated_boundary_jitter_m=4.5)

    assert isinstance(res, CadastralAdjudicationResult)
    assert res.boundary_iou < 1.0
    assert res.mean_boundary_displacement_m == 4.5
    assert res.encroachment_detected is True
    assert res.encroachment_area_m2 > 0.0
    assert res.recommended_title_haircut > 0.0
    assert "its4land_fcn_boundary_iou_adjudication" in res.lineage.processing_method
