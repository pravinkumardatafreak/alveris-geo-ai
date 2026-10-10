"""Tests for UN Sustainable Development Goals (SDG) and ESG Scorecard."""

import pytest

from alveris.core.lineage import DerivedFeatureLineage
from alveris.inundation.engine import InundationScenarioResult
from alveris.network.resilience import NetworkResilienceMetrics
from alveris.reporting.sdg_esg import UN_SDG_Scorecard, compute_un_sdg_scorecard
from alveris.sensors.multispectral import EnvironmentalStressMetrics, SpectralIndexStats
from alveris.subsidence.engine import (
    SettlementRiskLevel,
    SubsidenceMetrics,
    SubsidenceProjection,
)


@pytest.fixture
def mock_hazard_components():
    """Create mock physical hazard outputs for SDG scoring."""
    dummy_lineage = DerivedFeatureLineage(
        feature_name="test_inundation",
        source_dataset_ids=["copernicus_dem_glo_30"],
        processing_method="bathtub_connectivity_8dir",
        formula="elevation <= water_level",
        units="fraction",
        confidence=0.95,
        limitations=[],
    )
    inund = InundationScenarioResult(
        scenario_id="slr_1_0",
        water_level_rise_m=1.0,
        total_parcel_area_sqm=10000.0,
        flooded_area_sqm=2500.0,
        flooded_percent=25.0,
        usable_land_loss_sqm=2500.0,
        connected_inundation_fraction=0.25,
        flood_depth_mean_m=0.35,
        flood_depth_p90_m=0.75,
        max_flood_depth_m=0.85,
        unconnected_low_pocket_count=0,
        lineage=dummy_lineage,
    )
    subs = SubsidenceMetrics(
        min_subsidence_rate_mm_year=2.1,
        mean_subsidence_rate_mm_year=8.5,
        max_subsidence_rate_mm_year=14.2,
        differential_gradient_mm_per_m=0.0035,
        settlement_risk=SettlementRiskLevel.LOW,
        projection_2050=SubsidenceProjection(
            target_year=2050,
            projection_model="linear",
            cumulative_subsidence_m=0.21,
            effective_rslr_addition_m=0.21,
        ),
        projection_2100=SubsidenceProjection(
            target_year=2100,
            projection_model="linear",
            cumulative_subsidence_m=0.64,
            effective_rslr_addition_m=0.64,
        ),
        lineage=dummy_lineage,
    )
    idx = SpectralIndexStats(min_val=0.1, mean_val=0.45, median_val=0.42, max_val=0.8)
    stress = EnvironmentalStressMetrics(
        ndvi=idx,
        ndmi=idx,
        ndre=idx,
        ndvi_anomaly=-0.08,
        ndmi_anomaly=-0.05,
        ndre_anomaly=-0.04,
        vegetation_vigor_score=68.0,
        moisture_stress_score=35.0,
        salinization_risk_score=22.0,
        composite_environmental_stress_score=28.5,
        lineage=DerivedFeatureLineage(
            feature_name="test_stress",
            source_dataset_ids=["s2"],
            processing_method="spectral_indices",
            formula="test",
            units="index",
            confidence=0.9,
            limitations=[],
        ),
    )
    net = NetworkResilienceMetrics(
        scenario_id="slr_1_0",
        baseline_route_distance_m=1200.0,
        flooded_route_distance_m=1650.0,
        detour_ratio=1.375,
        is_physically_isolated=False,
        is_arterial_severed=False,
        impassable_edge_count=1,
        total_network_edges=8,
        network_accessibility_score=78.5,
        lineage=dummy_lineage,
    )
    return inund, subs, stress, net


def test_compute_un_sdg_scorecard(mock_hazard_components):
    """Verify UN SDG Scorecard evaluates 4 indicators and outputs compliant ESG tier."""
    inund, subs, stress, net = mock_hazard_components
    card = compute_un_sdg_scorecard(
        inundation=inund,
        subsidence=subs,
        stress=stress,
        network=net,
        cadastral_certainty_score=92.0,
    )

    assert isinstance(card, UN_SDG_Scorecard)
    assert len(card.indicators) == 4
    codes = [ind.indicator_code for ind in card.indicators]
    assert "SDG 1.4.2" in codes
    assert "SDG 11.5.1" in codes
    assert "SDG 13.1.1" in codes
    assert "SDG 15.3.1" in codes

    for ind in card.indicators:
        assert 0.0 <= ind.score <= 100.0
        assert ind.status in ["Compliant", "Substandard", "At Risk"]

    assert 0.0 <= card.composite_sdg_index <= 100.0
    assert "EU SFDR" in card.esg_eligibility_tier
    assert isinstance(card.green_bond_eligible, (bool, bool))
