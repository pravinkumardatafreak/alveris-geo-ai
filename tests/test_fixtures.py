"""Unit tests verifying sample GeoJSON fixtures and configuration files."""

import json
from pathlib import Path

import yaml

from alveris.core.spatial_gates import SpatialGateKeeper

SAMPLE_DIR = Path("data/sample")
CONFIG_DIR = Path("configs")


def test_sample_geojson_fixtures_valid():
    """Verify all 3 sample parcels exist, parse as valid GeoJSON, and pass Gate 3 checks."""
    fixtures = [
        "coastal_periurban_parcel.geojson",
        "agricultural_parcel.geojson",
        "inland_logistics_parcel.geojson",
    ]

    for filename in fixtures:
        filepath = SAMPLE_DIR / filename
        assert filepath.exists(), f"Missing fixture: {filepath}"

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) >= 1

        feature = data["features"][0]
        props = feature["properties"]
        geom = feature["geometry"]

        # Required properties check
        assert "asset_id" in props
        assert "name" in props
        assert "land_use_class" in props
        assert "baseline_market_value_inr" in props
        assert "utm_epsg" in props
        assert props["baseline_market_value_inr"] > 0

        # Geometry coordinates check
        coords = geom["coordinates"][0]  # Exterior ring
        SpatialGateKeeper.validate_geometry_coordinates(
            coordinates=coords,
            crs="EPSG:4326",
            feature_name=props["asset_id"],
        )

        # Tamil Nadu geographical bounding box sanity check: ~76-81°E, ~8-14°N
        for x, y in coords:
            assert 76.0 <= x <= 81.5, f"Longitude {x} outside Tamil Nadu region"
            assert 8.0 <= y <= 14.5, f"Latitude {y} outside Tamil Nadu region"


def test_configuration_files_parse_correctly():
    """Verify scenarios.yml, risk.yml, and valuation.yml load without error."""
    config_files = ["scenarios.yml", "risk.yml", "valuation.yml"]
    for config_name in config_files:
        filepath = CONFIG_DIR / config_name
        assert filepath.exists(), f"Missing config file: {filepath}"
        with open(filepath, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        assert "version" in cfg
