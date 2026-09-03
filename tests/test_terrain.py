"""Unit tests for Phase 3: Terrain & Elevation Engine."""

from pathlib import Path

import numpy as np
import pytest

from alveris.ingestion.parcel import load_parcel_from_geojson
from alveris.sample_data import (
    generate_coastal_dem_fixture,
    get_or_generate_dem_for_parcel,
)
from alveris.terrain.dem import compute_slope_grid, extract_parcel_terrain


@pytest.fixture
def coastal_dem(tmp_path: Path) -> Path:
    """Fixture providing a temporary synthetic coastal DEM."""
    dem_file = tmp_path / "test_coastal_dem.tif"
    return generate_coastal_dem_fixture(dem_file)


def test_terrain_extraction_on_coastal_parcel(coastal_dem: Path):
    """Verify elevation percentiles and slope computation over coastal parcel."""
    parcel = load_parcel_from_geojson("data/sample/coastal_periurban_parcel.geojson")

    metrics, clipped_band, transform = extract_parcel_terrain(
        dem_path=coastal_dem,
        parcel_geometry_wgs84=parcel.geometry_geojson,
    )

    assert metrics.pixel_count > 0
    assert metrics.elevation_min_m < metrics.elevation_max_m
    assert metrics.elevation_p05_m <= metrics.elevation_median_m <= metrics.elevation_p90_m
    assert metrics.slope_mean_deg >= 0.0
    assert metrics.relative_elevation_m == pytest.approx(
        metrics.elevation_max_m - metrics.elevation_min_m, abs=0.05
    )
    assert metrics.lineage.feature_name == "parcel_zonal_terrain_metrics"
    assert clipped_band.shape[0] > 0
    assert transform is not None


def test_terrain_extraction_on_agricultural_and_logistics_parcels(tmp_path: Path):
    """Verify terrain extraction works seamlessly on non-coastal inland parcels."""
    for sample_file in [
        "data/sample/agricultural_parcel.geojson",
        "data/sample/inland_logistics_parcel.geojson",
    ]:
        parcel = load_parcel_from_geojson(sample_file)
        dem = get_or_generate_dem_for_parcel(
            parcel.geometry_geojson, parcel.asset_id, output_dir=tmp_path
        )
        metrics, clipped_band, transform = extract_parcel_terrain(
            dem_path=dem, parcel_geometry_wgs84=parcel.geometry_geojson
        )
        assert metrics.pixel_count > 0
        assert metrics.elevation_median_m > 5.0
        assert clipped_band.shape[0] > 0
        assert transform is not None


def test_slope_gradient_computation():
    """Verify compute_slope_grid accurately calculates slope on known ramp."""
    # 10x10 elevation ramp: rises 10m over 100m horizontal distance (tan theta = 0.1, theta ~ 5.71 deg)
    x = np.linspace(0, 10, 10)
    grid = np.repeat(x[np.newaxis, :], 10, axis=0).astype(np.float32)

    slope = compute_slope_grid(grid, cell_size_x=10.0, cell_size_y=10.0)
    # Interior pixels slope should match ~5.7 degrees
    interior_slope = slope[2:8, 2:8]
    assert np.all(interior_slope > 5.0)
    assert np.all(interior_slope < 6.5)
