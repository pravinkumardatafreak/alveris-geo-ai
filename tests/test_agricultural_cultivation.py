"""Tests for Agricultural Field Cultivation Adjudication (Kerner et al., AAAI 2023)."""

import pytest

from alveris.ingestion.cadastre import (
    AgriculturalCultivationResult,
    adjudicate_agricultural_cultivation,
)
from alveris.ingestion.parcel import load_parcel_from_geojson


@pytest.fixture
def mock_parcel():
    """Load sample coastal parcel asset for testing."""
    return load_parcel_from_geojson("data/sample/coastal_periurban_parcel.geojson")


def test_fully_cultivated_parcel(mock_parcel):
    """Verify that >=90% active cultivation with high PIoU>=0.95 triggers zero haircut."""
    res = adjudicate_agricultural_cultivation(
        mock_parcel,
        simulated_cultivated_fraction=1.0,
        boundary_precision_iou_95=0.95,
    )

    assert isinstance(res, AgriculturalCultivationResult)
    assert res.is_fully_cultivated is True
    assert res.active_cultivated_ratio == 1.0
    assert res.precision_at_iou_95 == 0.95
    assert res.recommended_fallow_haircut == 0.0
    assert len(res.seasonal_composites_analyzed) == 3
    assert "st_unet_multi_region_field_boundary_segmentation" in res.lineage.processing_method


def test_fallow_abandoned_parcel(mock_parcel):
    """Verify that uncultivated/fallow fraction triggers proportional valuation haircut."""
    res = adjudicate_agricultural_cultivation(
        mock_parcel,
        simulated_cultivated_fraction=0.45,
        boundary_precision_iou_95=0.75,
    )

    assert isinstance(res, AgriculturalCultivationResult)
    assert res.is_fully_cultivated is False
    assert res.active_cultivated_ratio == 0.45
    assert res.recommended_fallow_haircut > 0.10
    assert res.precision_at_iou_95 == 0.75
    assert res.active_cultivated_area_ha < res.deed_area_ha
