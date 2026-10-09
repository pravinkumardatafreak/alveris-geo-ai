"""Unit tests for Folium interactive GIS mapping engine."""

import tempfile
from pathlib import Path
import folium

from alveris.core.lineage import DerivedFeatureLineage
from alveris.ingestion.parcel import load_parcel_from_geojson
from alveris.inundation.engine import InundationScenarioResult
from alveris.reporting.folium_map import create_alveris_folium_map, export_folium_map_to_html


def test_folium_map_generation_and_export():
    """Verify Folium map creates with GeoJSON layers and exports to valid HTML."""
    parcel = load_parcel_from_geojson("data/sample/coastal_periurban_parcel.geojson")
    lineage = DerivedFeatureLineage(
        feature_name="inundation",
        source_dataset_ids=["copernicus_dem"],
        processing_method="test",
        units="m",
        confidence=0.9,
    )
    inundation = InundationScenarioResult(
        scenario_id="slr_1_0",
        water_level_rise_m=1.0,
        total_parcel_area_sqm=10000.0,
        flooded_area_sqm=3000.0,
        flooded_percent=30.0,
        usable_land_loss_sqm=3000.0,
        connected_inundation_fraction=0.3,
        flood_depth_mean_m=0.5,
        flood_depth_p90_m=0.8,
        max_flood_depth_m=1.0,
        unconnected_low_pocket_count=0,
        lineage=lineage,
    )

    folium_map = create_alveris_folium_map(
        parcel=parcel,
        inundation=inundation,
        subsidence_rate_mm_yr=-9.2,
        is_network_severed=True,
    )

    assert isinstance(folium_map, folium.Map)
    
    # Verify HTML export
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_html = Path(tmp_dir) / "test_map.html"
        result_path = export_folium_map_to_html(folium_map, out_html)
        assert result_path.exists()
        html_text = result_path.read_text(encoding="utf-8")
        assert "leaflet" in html_text.lower()
        assert parcel.name in html_text
