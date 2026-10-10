"""Unit tests for Phase 9: Climate-Adjusted Valuation & Climate VaR Engine."""

import pytest

from alveris.core.lineage import DerivedFeatureLineage
from alveris.inundation.engine import InundationScenarioResult
from alveris.network.resilience import NetworkResilienceMetrics
from alveris.sensors.multispectral import (
    EnvironmentalStressMetrics,
    SpectralIndexStats,
)
from alveris.subsidence.engine import (
    SettlementRiskLevel,
    SubsidenceMetrics,
    SubsidenceProjection,
)
from alveris.valuation.engine import (
    PhysicalHazardInputs,
    ValuationModelConfig,
    evaluate_climate_valuation,
)


@pytest.fixture
def dummy_lineage():
    return DerivedFeatureLineage(
        feature_name="test_feature",
        source_dataset_ids=["test_source"],
        processing_method="unit_test",
        formula="x = y",
        units="unit",
        confidence=0.9,
    )


@pytest.fixture
def baseline_inputs(dummy_lineage):
    inundation = InundationScenarioResult(
        scenario_id="baseline",
        water_level_rise_m=0.0,
        total_parcel_area_sqm=10000.0,
        flooded_area_sqm=0.0,
        flooded_percent=0.0,
        usable_land_loss_sqm=0.0,
        connected_inundation_fraction=0.0,
        flood_depth_mean_m=0.0,
        flood_depth_p90_m=0.0,
        max_flood_depth_m=0.0,
        unconnected_low_pocket_count=0,
        lineage=dummy_lineage,
    )
    subsidence = SubsidenceMetrics(
        mean_subsidence_rate_mm_year=0.0,
        min_subsidence_rate_mm_year=0.0,
        max_subsidence_rate_mm_year=0.0,
        differential_gradient_mm_per_m=0.0,
        settlement_risk=SettlementRiskLevel.NEGLIGIBLE,
        projection_2050=SubsidenceProjection(
            target_year=2050,
            projection_model="linear",
            cumulative_subsidence_m=0.0,
            effective_rslr_addition_m=0.0,
        ),
        projection_2100=SubsidenceProjection(
            target_year=2100,
            projection_model="linear",
            cumulative_subsidence_m=0.0,
            effective_rslr_addition_m=0.0,
        ),
        lineage=dummy_lineage,
    )
    idx_stat = SpectralIndexStats(min_val=0.6, mean_val=0.7, median_val=0.7, max_val=0.8)
    environment = EnvironmentalStressMetrics(
        ndvi=idx_stat,
        ndmi=idx_stat,
        ndre=idx_stat,
        ndvi_anomaly=0.0,
        ndmi_anomaly=0.0,
        ndre_anomaly=0.0,
        vegetation_vigor_score=100.0,
        moisture_stress_score=0.0,
        salinization_risk_score=0.0,
        composite_environmental_stress_score=0.0,
        lineage=dummy_lineage,
    )
    network = NetworkResilienceMetrics(
        scenario_id="baseline",
        baseline_route_distance_m=1000.0,
        flooded_route_distance_m=1000.0,
        detour_ratio=1.0,
        is_physically_isolated=False,
        impassable_edge_count=0,
        total_network_edges=5,
        network_accessibility_score=100.0,
        lineage=dummy_lineage,
    )
    return PhysicalHazardInputs(
        inundation=inundation,
        subsidence=subsidence,
        environment=environment,
        network=network,
    )


def test_zero_loss_under_baseline(baseline_inputs):
    """Verify that unexposed baseline conditions incur zero valuation haircut."""
    val = evaluate_climate_valuation(
        baseline_market_value_inr=10000000.0,  # 1 Crore INR
        hazards=baseline_inputs,
    )

    assert val.climate_adjusted_value_inr == 10000000.0
    assert val.deductions.total_haircut_inr == 0.0
    assert val.deductions.total_haircut_percent == 0.0
    assert val.climate_var_proxy_inr == 0.0


def test_inundation_land_loss_haircut(baseline_inputs, dummy_lineage):
    """Verify direct land loss deduction scales with submerged area fraction."""
    # 40% usable land loss on 10M INR parcel -> 4M INR deduction
    inundation_40pct = InundationScenarioResult(
        scenario_id="slr_1_0",
        water_level_rise_m=1.0,
        total_parcel_area_sqm=10000.0,
        flooded_area_sqm=4000.0,
        flooded_percent=40.0,
        usable_land_loss_sqm=4000.0,
        connected_inundation_fraction=0.4,
        flood_depth_mean_m=0.8,
        flood_depth_p90_m=1.0,
        max_flood_depth_m=1.2,
        unconnected_low_pocket_count=0,
        lineage=dummy_lineage,
    )

    hazards = PhysicalHazardInputs(
        inundation=inundation_40pct,
        subsidence=baseline_inputs.subsidence,
        environment=baseline_inputs.environment,
        network=baseline_inputs.network,
    )

    val = evaluate_climate_valuation(
        baseline_market_value_inr=10000000.0,
        hazards=hazards,
    )

    assert val.deductions.inundation_loss_inr == pytest.approx(4000000.0, abs=1.0)
    assert val.climate_adjusted_value_inr == pytest.approx(6000000.0, abs=1.0)
    assert val.climate_var_percent == pytest.approx(40.0, abs=0.1)


def test_road_network_isolation_penalty(baseline_inputs, dummy_lineage):
    """Verify 40% valuation haircut when site is completely severed from highway network."""
    severed_network = NetworkResilienceMetrics(
        scenario_id="slr_1_5",
        baseline_route_distance_m=1000.0,
        flooded_route_distance_m=None,
        detour_ratio=10.0,
        is_physically_isolated=True,
        impassable_edge_count=2,
        total_network_edges=5,
        network_accessibility_score=0.0,
        lineage=dummy_lineage,
    )

    hazards = PhysicalHazardInputs(
        inundation=baseline_inputs.inundation,
        subsidence=baseline_inputs.subsidence,
        environment=baseline_inputs.environment,
        network=severed_network,
    )

    val = evaluate_climate_valuation(
        baseline_market_value_inr=10000000.0,
        hazards=hazards,
    )

    # 40% isolation penalty on 10M INR = 4M INR deduction
    assert val.deductions.accessibility_penalty_inr == pytest.approx(4000000.0, abs=1.0)
    assert val.climate_adjusted_value_inr == pytest.approx(6000000.0, abs=1.0)


def test_maximum_haircut_cap(baseline_inputs, dummy_lineage):
    """Verify total deductions are capped at 85% to preserve residual salvage value."""
    # 90% direct flood loss + severed network (40%) = 130% theoretical loss
    catastrophic_inundation = InundationScenarioResult(
        scenario_id="slr_2_0",
        water_level_rise_m=2.0,
        total_parcel_area_sqm=10000.0,
        flooded_area_sqm=9000.0,
        flooded_percent=90.0,
        usable_land_loss_sqm=9000.0,
        connected_inundation_fraction=0.9,
        flood_depth_mean_m=2.0,
        flood_depth_p90_m=2.3,
        max_flood_depth_m=2.5,
        unconnected_low_pocket_count=0,
        lineage=dummy_lineage,
    )
    catastrophic_network = NetworkResilienceMetrics(
        scenario_id="slr_2_0",
        baseline_route_distance_m=1000.0,
        flooded_route_distance_m=None,
        detour_ratio=10.0,
        is_physically_isolated=True,
        impassable_edge_count=3,
        total_network_edges=5,
        network_accessibility_score=0.0,
        lineage=dummy_lineage,
    )

    hazards = PhysicalHazardInputs(
        inundation=catastrophic_inundation,
        subsidence=baseline_inputs.subsidence,
        environment=baseline_inputs.environment,
        network=catastrophic_network,
    )

    val = evaluate_climate_valuation(
        baseline_market_value_inr=10000000.0,
        hazards=hazards,
        config=ValuationModelConfig(max_haircut_cap_percent=85.0),
    )

    # Haircut capped at 85% (8.5M INR), residual salvage value = 15% (1.5M INR)
    assert val.deductions.total_haircut_inr == pytest.approx(8500000.0, abs=1.0)
    assert val.climate_adjusted_value_inr == pytest.approx(1500000.0, abs=1.0)
    assert val.deductions.total_haircut_percent == 85.0
    assert len(val.waterfall_breakdown) == 6
