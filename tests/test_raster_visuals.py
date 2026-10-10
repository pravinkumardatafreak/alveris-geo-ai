"""Unit tests for PyDeck map layers and 2D Earth Observation raster visualizers."""

import numpy as np

from alveris.core.lineage import DerivedFeatureLineage
from alveris.ingestion.parcel import load_parcel_from_geojson
from alveris.inundation.engine import InundationScenarioResult
from alveris.reporting.map_layers import (
    MapLayerOptions,
    create_alveris_deck_map,
)
from alveris.reporting.rasters import (
    plot_dem_elevation_raster,
    plot_insar_subsidence_surface,
    plot_sentinel2_false_color_cir,
    plot_slope_gradient_raster,
)


def test_pydeck_map_generation():
    """Verify PyDeck Deck object builds with layers and valid initial view state."""
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

    deck = create_alveris_deck_map(
        parcel=parcel,
        inundation=inundation,
        is_network_isolated=True,
        options=MapLayerOptions(show_flood_extent=True, show_road_network=True),
    )
    assert deck is not None
    assert len(deck.layers) == 3  # Parcel polygon + Flood polygon + Road network


def test_raster_visual_figures():
    """Verify 2D Matplotlib raster visualizers produce non-empty figures."""
    elevation_grid = np.linspace(0.2, 3.5, 400).reshape((20, 20))
    slope_grid = np.abs(np.gradient(elevation_grid)[0]) * 10.0

    fig_dem = plot_dem_elevation_raster(elevation_grid, water_level_rise_m=1.0)
    assert fig_dem is not None
    assert len(fig_dem.axes) > 0

    fig_slope = plot_slope_gradient_raster(slope_grid)
    assert fig_slope is not None
    assert len(fig_slope.axes) > 0

    tensor_4band = np.random.uniform(0.1, 0.8, (4, 20, 20)).astype(np.float32)
    fig_cir = plot_sentinel2_false_color_cir(tensor_4band)
    assert fig_cir is not None
    assert len(fig_cir.axes) > 0

    fig_insar = plot_insar_subsidence_surface(mean_rate_mm=12.0, differential_gradient=0.15)
    assert fig_insar is not None
    assert len(fig_insar.axes) > 0
