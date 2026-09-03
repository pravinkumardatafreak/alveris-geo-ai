"""Unit tests for Phase 8: Risk Scoring & Explainability Engine."""

import pytest

from alveris.core.lineage import DerivedFeatureLineage
from alveris.inundation.engine import InundationScenarioResult
from alveris.network.resilience import NetworkResilienceMetrics
from alveris.risk.scoring import (
    RiskTier,
    RiskWeightsConfig,
    classify_risk_tier,
    compute_inundation_score,
    compute_network_score,
    compute_subsidence_score,
    evaluate_composite_risk,
)
from alveris.sensors.multispectral import (
    EnvironmentalStressMetrics,
    SpectralIndexStats,
)
from alveris.subsidence.engine import (
    SettlementRiskLevel,
    SubsidenceMetrics,
    SubsidenceProjection,
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


def test_component_score_calculations(dummy_lineage):
    """Verify mathematical scaling of individual component hazard scores."""
    # Inundation: 50% flooded area, 1.0m mean depth -> 0.6*50 + 0.4*(1.0/2.0*100) = 30 + 20 = 50.0
    inundation = InundationScenarioResult(
        scenario_id="test",
        water_level_rise_m=1.0,
        total_parcel_area_sqm=10000.0,
        flooded_area_sqm=5000.0,
        flooded_percent=50.0,
        usable_land_loss_sqm=5000.0,
        connected_inundation_fraction=0.5,
        flood_depth_mean_m=1.0,
        flood_depth_p90_m=1.2,
        max_flood_depth_m=1.5,
        unconnected_low_pocket_count=0,
        lineage=dummy_lineage,
    )
    assert compute_inundation_score(inundation) == pytest.approx(50.0, abs=0.1)

    # Subsidence: 10 mm/yr rate (rate_score = 50), Low settlement risk (bonus = 15)
    # 0.7*50 + 0.3*15 = 35 + 4.5 = 39.5
    subsidence = SubsidenceMetrics(
        mean_subsidence_rate_mm_year=10.0,
        min_subsidence_rate_mm_year=8.0,
        max_subsidence_rate_mm_year=12.0,
        differential_gradient_mm_per_m=0.10,
        settlement_risk=SettlementRiskLevel.LOW,
        projection_2050=SubsidenceProjection(
            target_year=2050,
            projection_model="linear",
            cumulative_subsidence_m=0.25,
            effective_rslr_addition_m=0.25,
        ),
        projection_2100=SubsidenceProjection(
            target_year=2100,
            projection_model="linear",
            cumulative_subsidence_m=0.75,
            effective_rslr_addition_m=0.75,
        ),
        lineage=dummy_lineage,
    )
    assert compute_subsidence_score(subsidence) == pytest.approx(39.5, abs=0.1)

    # Network: accessibility score = 70.0 -> disruption score = 100 - 70 = 30.0
    network = NetworkResilienceMetrics(
        scenario_id="test",
        baseline_route_distance_m=1000.0,
        flooded_route_distance_m=1400.0,
        detour_ratio=1.4,
        is_physically_isolated=False,
        impassable_edge_count=1,
        total_network_edges=10,
        network_accessibility_score=70.0,
        lineage=dummy_lineage,
    )
    assert compute_network_score(network) == 30.0


def test_classify_risk_tier():
    """Verify tier assignment across all threshold boundaries."""
    assert classify_risk_tier(15.0) == RiskTier.LOW
    assert classify_risk_tier(25.0) == RiskTier.MODERATE
    assert classify_risk_tier(45.0) == RiskTier.ELEVATED
    assert classify_risk_tier(65.0) == RiskTier.HIGH
    assert classify_risk_tier(85.0) == RiskTier.EXTREME


def test_evaluate_composite_risk_end_to_end(dummy_lineage):
    """Verify weighted synthesis, primary driver identification, and explainability text."""
    inundation = InundationScenarioResult(
        scenario_id="slr_2_0",
        water_level_rise_m=2.0,
        total_parcel_area_sqm=10000.0,
        flooded_area_sqm=8000.0,
        flooded_percent=80.0,
        usable_land_loss_sqm=8000.0,
        connected_inundation_fraction=0.8,
        flood_depth_mean_m=1.8,
        flood_depth_p90_m=2.1,
        max_flood_depth_m=2.5,
        unconnected_low_pocket_count=0,
        lineage=dummy_lineage,
    )
    subsidence = SubsidenceMetrics(
        mean_subsidence_rate_mm_year=12.0,
        min_subsidence_rate_mm_year=10.0,
        max_subsidence_rate_mm_year=14.0,
        differential_gradient_mm_per_m=0.25,
        settlement_risk=SettlementRiskLevel.MODERATE,
        projection_2050=SubsidenceProjection(
            target_year=2050,
            projection_model="linear",
            cumulative_subsidence_m=0.3,
            effective_rslr_addition_m=0.3,
        ),
        projection_2100=SubsidenceProjection(
            target_year=2100,
            projection_model="linear",
            cumulative_subsidence_m=0.9,
            effective_rslr_addition_m=0.9,
        ),
        lineage=dummy_lineage,
    )
    idx_stat = SpectralIndexStats(min_val=0.1, mean_val=0.2, median_val=0.2, max_val=0.3)
    environment = EnvironmentalStressMetrics(
        ndvi=idx_stat,
        ndmi=idx_stat,
        ndre=idx_stat,
        ndvi_anomaly=-0.35,
        ndmi_anomaly=-0.20,
        ndre_anomaly=-0.25,
        vegetation_vigor_score=20.0,
        moisture_stress_score=75.0,
        salinization_risk_score=80.0,
        composite_environmental_stress_score=78.2,
        lineage=dummy_lineage,
    )
    network = NetworkResilienceMetrics(
        scenario_id="slr_2_0",
        baseline_route_distance_m=1000.0,
        flooded_route_distance_m=None,
        detour_ratio=10.0,
        is_physically_isolated=True,
        impassable_edge_count=3,
        total_network_edges=8,
        network_accessibility_score=0.0,
        lineage=dummy_lineage,
    )

    assessment = evaluate_composite_risk(
        inundation=inundation,
        subsidence=subsidence,
        environment=environment,
        network=network,
        weights=RiskWeightsConfig(
            weight_inundation=0.40,
            weight_subsidence=0.20,
            weight_environmental=0.20,
            weight_network=0.20,
        ),
    )

    # Severe stress across all pillars -> composite risk score should be in High or Extreme tier
    assert assessment.composite_risk_score >= 60.0
    assert assessment.risk_tier in [RiskTier.HIGH, RiskTier.EXTREME]
    assert assessment.confidence_score_percent > 85.0
    assert assessment.primary_risk_driver != ""
    assert len(assessment.key_risk_factors) >= 3
    assert "slr_2_0" in assessment.executive_summary
