"""Unit tests for ALVERIS Data Lineage models."""

import pytest
from pydantic import ValidationError

from alveris.core.lineage import DataMode, DatasetLineage, DerivedFeatureLineage


def test_dataset_lineage_creation():
    """Verify valid DatasetLineage instantiates with default timestamps and data modes."""
    lineage = DatasetLineage(
        dataset_id="copernicus_dem_glo30_tn",
        provider="Copernicus / ESA",
        acquisition_date="2020-01-01 to 2024-12-31",
        crs="EPSG:4326",
        vertical_datum="EGM2008",
        resolution="30m",
        units="meters",
        nodata=-9999.0,
    )
    assert lineage.dataset_id == "copernicus_dem_glo30_tn"
    assert lineage.data_mode == DataMode.OBSERVED
    assert lineage.crs == "EPSG:4326"
    assert lineage.vertical_datum == "EGM2008"


def test_dataset_lineage_invalid_crs():
    """Verify that malformed or non-standard CRS values are rejected."""
    with pytest.raises(ValidationError):
        DatasetLineage(
            dataset_id="test_invalid",
            provider="Unknown",
            acquisition_date="2024-01-01",
            crs="invalid_crs_string",  # Does not specify EPSG: or UTM
            vertical_datum="EGM2008",
            resolution="10m",
            units="meters",
        )


def test_derived_feature_lineage():
    """Verify DerivedFeatureLineage tracks formula, source datasets, and confidence bounds."""
    derived = DerivedFeatureLineage(
        feature_name="connected_inundation_fraction",
        source_dataset_ids=["copernicus_dem_glo30_tn"],
        processing_method="8_way_connectivity_flood_fill",
        formula="inundated_connected_pixels / total_parcel_pixels",
        units="fraction 0-1",
        scenario_id="slr_1_0",
        confidence=0.88,
        limitations=["Assumes static hydrodynamic boundary conditions without storm surge"],
    )
    assert derived.confidence == 0.88
    assert derived.scenario_id == "slr_1_0"
    assert len(derived.limitations) == 1
    assert len(derived.provenance_hash) == 16


def test_provenance_hash_is_deterministic():
    """Verify that provenance hashes are deterministic SHA-256 strings."""
    lineage = DatasetLineage(
        dataset_id="copernicus_dem_glo30_tn",
        provider="Copernicus / ESA",
        acquisition_date="2020-01-01 to 2024-12-31",
        crs="EPSG:4326",
        vertical_datum="EGM2008",
        resolution="30m",
        units="meters",
    )
    assert len(lineage.provenance_hash) == 16
    assert lineage.provenance_hash == lineage.provenance_hash

