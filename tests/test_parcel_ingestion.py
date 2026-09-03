"""Unit tests for Phase 2: Parcel Vector Ingestion & CRS Governance."""

from pathlib import Path

import pytest

from alveris.core.spatial_gates import SpatialIntegrityError
from alveris.ingestion.parcel import get_utm_epsg_from_lonlat, load_parcel_from_geojson

SAMPLE_DIR = Path("data/sample")


def test_utm_zone_derivation():
    """Verify UTM zone EPSG calculation across various global coordinates."""
    # Chennai / Tamil Nadu (lon 80.3°, lat 13.1° N) -> Zone 44 N
    assert get_utm_epsg_from_lonlat(80.3, 13.1) == "EPSG:32644"

    # Mumbai (lon 72.8°, lat 18.9° N) -> Zone 43 N
    assert get_utm_epsg_from_lonlat(72.8, 18.9) == "EPSG:32643"

    # New York (lon -74.0°, lat 40.7° N) -> Zone 18 N
    assert get_utm_epsg_from_lonlat(-74.0, 40.7) == "EPSG:32618"

    # Sydney, Australia (lon 151.2°, lat -33.8° S) -> Zone 56 S
    assert get_utm_epsg_from_lonlat(151.2, -33.8) == "EPSG:32756"

    # Out of range latitudes/longitudes must raise error
    with pytest.raises(SpatialIntegrityError):
        get_utm_epsg_from_lonlat(200.0, 10.0)


def test_load_sample_coastal_parcel():
    """Verify ingestion of coastal peri-urban parcel with automated UTM projection."""
    file_path = SAMPLE_DIR / "coastal_periurban_parcel.geojson"
    asset = load_parcel_from_geojson(file_path)

    assert asset.asset_id == "ALV-TN-CP01"
    assert asset.land_use_class == "periurban_residential"
    assert asset.utm_epsg == "EPSG:32644"
    assert asset.area_sqm > 50000.0
    assert asset.area_hectares > 5.0
    assert asset.area_acres > 12.0

    # Bounds check
    minx, miny, maxx, maxy = asset.bounds_wgs84
    assert 80.31 <= minx < maxx <= 80.32
    assert 13.24 <= miny < maxy <= 13.25

    # Centroid check
    cen_lon, cen_lat = asset.centroid_wgs84
    assert minx < cen_lon < maxx
    assert miny < cen_lat < maxy

    # Lineage check
    assert asset.lineage.dataset_id == "cadastral_ALV-TN-CP01"
    assert asset.lineage.crs == "EPSG:4326"


def test_load_all_sample_parcels():
    """Verify all 3 sample parcels load and calculate valid metric areas."""
    files = [
        "coastal_periurban_parcel.geojson",
        "agricultural_parcel.geojson",
        "inland_logistics_parcel.geojson",
    ]

    for fname in files:
        asset = load_parcel_from_geojson(SAMPLE_DIR / fname)
        assert asset.area_sqm > 1000.0
        assert asset.area_hectares == pytest.approx(asset.area_sqm / 10000.0, rel=1e-3)
        assert asset.area_acres == pytest.approx(asset.area_sqm / 4046.8564224, rel=1e-3)
        assert asset.baseline_market_value_inr > 0


def test_load_missing_file_raises_error():
    """Verify non-existent file path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_parcel_from_geojson("data/sample/non_existent_file.geojson")
