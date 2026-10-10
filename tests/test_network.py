"""Unit tests for Phase 7: Road Network Resilience & Evacuation Detour Engine."""

import pytest

from alveris.network.resilience import (
    NetworkEvaluationConfig,
    RoadNetworkResilienceEngine,
)
from alveris.sample_data import generate_sample_road_network_fixture


def test_dry_baseline_shortest_path_routing():
    """Verify optimal baseline access without flood disruption."""
    graph = generate_sample_road_network_fixture()
    engine = RoadNetworkResilienceEngine()

    # Dry conditions: all edge flood depths = 0.0m
    edge_depths = {(0, 1): 0.0, (1, 2): 0.0, (0, 3): 0.0, (3, 2): 0.0}

    metrics = engine.evaluate_route_resilience(
        base_graph=graph,
        origin_node=0,
        destination_node=2,
        edge_flood_depths=edge_depths,
        scenario_id="baseline",
    )

    # Shortest path is 0 -> 1 -> 2: 500m + 1000m = 1500m
    assert metrics.baseline_route_distance_m == 1500.0
    assert metrics.flooded_route_distance_m == 1500.0
    assert metrics.detour_ratio == 1.0
    assert not metrics.is_physically_isolated
    assert metrics.impassable_edge_count == 0
    assert metrics.network_accessibility_score == 100.0


def test_flooded_arterial_triggers_inland_detour():
    """Verify routing through secondary detour when primary coastal road is submerged."""
    graph = generate_sample_road_network_fixture()
    engine = RoadNetworkResilienceEngine(
        config=NetworkEvaluationConfig(passability_depth_threshold_m=0.30)
    )

    # Edge (1, 2) is submerged under 0.65m of floodwater (impassable)
    # Inland detour via (0, 3) and (3, 2) remains dry (0.0m)
    edge_depths = {(0, 1): 0.0, (1, 2): 0.65, (0, 3): 0.0, (3, 2): 0.0}

    metrics = engine.evaluate_route_resilience(
        base_graph=graph,
        origin_node=0,
        destination_node=2,
        edge_flood_depths=edge_depths,
        scenario_id="slr_1_0",
    )

    # Baseline was 1500m; new detour via (0 -> 3 -> 2) is 800m + 1500m = 2300m
    assert metrics.baseline_route_distance_m == 1500.0
    assert metrics.flooded_route_distance_m == 2300.0
    # Detour ratio = 2300 / 1500 = 1.53
    assert metrics.detour_ratio == pytest.approx(1.53, abs=0.01)
    assert not metrics.is_physically_isolated
    assert metrics.impassable_edge_count == 1
    # Accessibility score penalizes detour length
    assert 80.0 <= metrics.network_accessibility_score <= 95.0


def test_complete_physical_isolation_when_all_access_severed():
    """Verify isolation detection and zero accessibility score when all paths are blocked."""
    graph = generate_sample_road_network_fixture()
    engine = RoadNetworkResilienceEngine(
        config=NetworkEvaluationConfig(passability_depth_threshold_m=0.30)
    )

    # Both exits from Node 0 are submerged: (0, 1) has 0.45m depth, (0, 3) has 0.50m depth
    edge_depths = {(0, 1): 0.45, (1, 2): 0.65, (0, 3): 0.50, (3, 2): 0.0}

    metrics = engine.evaluate_route_resilience(
        base_graph=graph,
        origin_node=0,
        destination_node=2,
        edge_flood_depths=edge_depths,
        scenario_id="slr_2_0",
    )

    assert metrics.is_physically_isolated
    assert metrics.flooded_route_distance_m is None
    assert metrics.detour_ratio == 10.0
    assert metrics.network_accessibility_score == 0.0
    assert metrics.impassable_edge_count >= 2


def test_shallow_water_remains_passable():
    """Verify vehicles can pass through minor road water ponding below threshold."""
    graph = generate_sample_road_network_fixture()
    engine = RoadNetworkResilienceEngine(
        config=NetworkEvaluationConfig(passability_depth_threshold_m=0.30)
    )

    # Coastal road has 0.12m of water (below 0.30m threshold)
    edge_depths = {(0, 1): 0.05, (1, 2): 0.12, (0, 3): 0.0, (3, 2): 0.0}

    metrics = engine.evaluate_route_resilience(
        base_graph=graph,
        origin_node=0,
        destination_node=2,
        edge_flood_depths=edge_depths,
        scenario_id="slr_0_5",
    )

    assert not metrics.is_physically_isolated
    assert metrics.impassable_edge_count == 0
    assert metrics.detour_ratio == 1.0
    assert metrics.network_accessibility_score == 100.0
