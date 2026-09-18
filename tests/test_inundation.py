"""Unit tests for Phase 4: Connected Inundation & SLR Engine."""

import numpy as np

from alveris.inundation.engine import (
    ConnectedInundationEngine,
    ScenarioParameters,
)


def test_connected_vs_isolated_depression_inundation():
    """Verify that Level 2 connected inundation protects isolated inland depressions behind ridges."""
    engine = ConnectedInundationEngine(connectivity_mode="8_way")

    # 1D slice concept expanded to 7x7 grid:
    # Column 0-1: Low coast (0.2m)
    # Column 2-3: Elevated protective dyke/ridge (2.5m)
    # Column 4-6: Low inland bowl (0.4m)
    grid = np.zeros((7, 7), dtype=np.float32)
    grid[:, 0:2] = 0.2
    grid[:, 2:4] = 2.5
    grid[:, 4:7] = 0.4

    # Ocean seed is at the western coast (column 0)
    ocean_seed = np.zeros((7, 7), dtype=bool)
    ocean_seed[:, 0] = True

    # Scenario: +1.0m water level rise
    connected_flood, unconnected_pockets, depth_grid = engine.compute_connected_flood(
        elevation_grid=grid,
        water_threshold_m=1.0,
        ocean_seed_mask=ocean_seed,
    )

    # Coast is flooded
    assert np.all(connected_flood[:, 0:2])
    # Ridge is dry
    assert not np.any(connected_flood[:, 2:4])
    # Inland bowl is PROTECTED by the ridge!
    assert not np.any(connected_flood[:, 4:7])
    # Inland bowl is correctly classified as an unconnected low pocket
    assert np.all(unconnected_pockets[:, 4:7])

    # Water depth on flooded coast: 1.0m - 0.2m = 0.8m
    assert np.allclose(depth_grid[:, 0:2], 0.8, atol=1e-3)


def test_monotonic_scenario_inundation():
    """Verify that higher SLR scenarios result in monotonically increasing flood extents."""
    engine = ConnectedInundationEngine(connectivity_mode="8_way")

    # Gentle coastal ramp from 0.0m (East) to 3.0m (West)
    x = np.linspace(3.0, 0.0, 30)
    grid = np.repeat(x[np.newaxis, :], 30, axis=0).astype(np.float32)

    ocean_seed = np.zeros((30, 30), dtype=bool)
    ocean_seed[:, -1] = True  # Eastern edge is sea

    parcel_mask = np.ones((30, 30), dtype=bool)

    scenarios = [0.5, 1.0, 1.5, 2.0]
    previous_flooded_area = -1.0

    for slr in scenarios:
        params = ScenarioParameters(
            water_level_rise_m=slr,
            pixel_area_sqm=900.0,
            scenario_id=f"slr_{str(slr).replace('.', '_')}",
        )
        res, _, _ = engine.evaluate_parcel_scenario(
            elevation_grid=grid,
            parcel_mask=parcel_mask,
            ocean_seed_mask=ocean_seed,
            params=params,
        )
        assert res.flooded_area_sqm > previous_flooded_area
        assert res.flooded_percent >= 0.0
        assert res.usable_land_loss_sqm == res.flooded_area_sqm
        previous_flooded_area = res.flooded_area_sqm


def test_subsidence_increases_effective_flood_depth():
    """Verify that land subsidence compounds flood depth and extent."""
    engine = ConnectedInundationEngine()

    grid = np.full((10, 10), 1.2, dtype=np.float32)
    ocean_seed = np.zeros((10, 10), dtype=bool)
    ocean_seed[:, 0] = True

    # At +1.0m SLR without subsidence: elevation 1.2m remains DRY
    flood_no_sub, _, _ = engine.compute_connected_flood(
        elevation_grid=grid,
        water_threshold_m=1.0,
        ocean_seed_mask=ocean_seed,
        subsidence_grid_m=None,
    )
    assert not np.any(flood_no_sub)

    # With 0.4m subsidence: effective elevation drops to 0.8m (1.2 - 0.4), becoming SUBMERGED under 1.0m water!
    subsidence = np.full((10, 10), 0.4, dtype=np.float32)
    flood_with_sub, _, depths = engine.compute_connected_flood(
        elevation_grid=grid,
        water_threshold_m=1.0,
        ocean_seed_mask=ocean_seed,
        subsidence_grid_m=subsidence,
    )
    assert np.all(flood_with_sub)
    # Flood depth = 1.0 - (1.2 - 0.4) = 0.2m
    assert np.allclose(depths, 0.2, atol=1e-3)
