"""Unit tests for Phase 10 & Phase 11: Reporting & Visualization Engine."""

from pathlib import Path

import pytest

from alveris.core.lineage import DerivedFeatureLineage
from alveris.ingestion.parcel import load_parcel_from_geojson
from alveris.inundation.engine import InundationScenarioResult
from alveris.models.multispectral_cnn import (
    LandCoverClass,
    ZoningVerificationResult,
)
from alveris.network.resilience import NetworkResilienceMetrics
from alveris.reporting.charts import (
    create_risk_pillar_chart,
    create_scenario_comparison_chart,
    create_subsidence_trajectory_chart,
    create_valuation_waterfall_chart,
    create_zoning_confidence_chart,
)
from alveris.reporting.memo import (
    export_memo_to_file,
    generate_html_underwriting_memo,
    generate_markdown_underwriting_memo,
)
from alveris.risk.scoring import evaluate_composite_risk
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
    evaluate_climate_valuation,
)


@pytest.fixture
def mock_valuation_and_risk():
    """Build mock parcel, valuation, and risk objects for reporting tests."""
    parcel = load_parcel_from_geojson("data/sample/coastal_periurban_parcel.geojson")

    lineage = DerivedFeatureLineage(
        feature_name="test_memo_feature",
        source_dataset_ids=["copernicus_dem_glo30"],
        processing_method="unit_test_simulation",
        formula="y = f(x)",
        units="unit",
        confidence=0.92,
    )

    inundation = InundationScenarioResult(
        scenario_id="slr_1_0",
        water_level_rise_m=1.0,
        total_parcel_area_sqm=10000.0,
        flooded_area_sqm=3500.0,
        flooded_percent=35.0,
        usable_land_loss_sqm=3500.0,
        connected_inundation_fraction=0.35,
        flood_depth_mean_m=0.75,
        flood_depth_p90_m=1.1,
        max_flood_depth_m=1.3,
        unconnected_low_pocket_count=0,
        lineage=lineage,
    )
    subsidence = SubsidenceMetrics(
        mean_subsidence_rate_mm_year=10.0,
        min_subsidence_rate_mm_year=8.0,
        max_subsidence_rate_mm_year=12.0,
        differential_gradient_mm_per_m=0.15,
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
        lineage=lineage,
    )
    idx_stat = SpectralIndexStats(min_val=0.2, mean_val=0.3, median_val=0.3, max_val=0.4)
    environment = EnvironmentalStressMetrics(
        ndvi=idx_stat,
        ndmi=idx_stat,
        ndre=idx_stat,
        ndvi_anomaly=-0.25,
        ndmi_anomaly=-0.15,
        ndre_anomaly=-0.18,
        vegetation_vigor_score=35.0,
        moisture_stress_score=60.0,
        salinization_risk_score=65.0,
        composite_environmental_stress_score=63.2,
        lineage=lineage,
    )
    network = NetworkResilienceMetrics(
        scenario_id="slr_1_0",
        baseline_route_distance_m=1200.0,
        flooded_route_distance_m=1800.0,
        detour_ratio=1.5,
        is_physically_isolated=False,
        impassable_edge_count=1,
        total_network_edges=6,
        network_accessibility_score=85.0,
        lineage=lineage,
    )

    risk = evaluate_composite_risk(
        inundation=inundation,
        subsidence=subsidence,
        environment=environment,
        network=network,
    )
    hazards = PhysicalHazardInputs(
        inundation=inundation,
        subsidence=subsidence,
        environment=environment,
        network=network,
    )
    val = evaluate_climate_valuation(
        baseline_market_value_inr=parcel.baseline_market_value_inr,
        hazards=hazards,
    )
    return parcel, val, risk, subsidence


def test_html_memo_generation_and_export(mock_valuation_and_risk, tmp_path: Path):
    """Verify HTML memo formatting, financial values, and file export."""
    parcel, val, risk, _ = mock_valuation_and_risk

    memo_html = generate_html_underwriting_memo(
        parcel=parcel,
        valuation=val,
        risk=risk,
    )

    assert "<!DOCTYPE html>" in memo_html
    assert parcel.asset_id in memo_html
    assert "ALVERIS Underwriting Memo" in memo_html
    assert "1. Executive Summary & Underwriting Assessment" in memo_html
    assert "3. Financial Valuation Waterfall (INR)" in memo_html

    out_file = tmp_path / "test_memo.html"
    res_path = export_memo_to_file(out_file, parcel, val, risk)
    assert res_path.exists()
    assert res_path.stat().st_size > 1000


def test_markdown_memo_generation_and_export(mock_valuation_and_risk, tmp_path: Path):
    """Verify Markdown memo formatting and .md file export."""
    parcel, val, risk, _ = mock_valuation_and_risk

    memo_md = generate_markdown_underwriting_memo(
        parcel=parcel,
        valuation=val,
        risk=risk,
    )

    assert f"# INSTITUTIONAL UNDERWRITING MEMO: {parcel.name.upper()}" in memo_md
    assert "## 1. Executive Summary & Regulatory KPIs" in memo_md
    assert "## 3. Financial Deduction Waterfall (INR)" in memo_md
    assert "INR" in memo_md

    out_md = tmp_path / "test_memo.md"
    res_path = export_memo_to_file(out_md, parcel, val, risk)
    assert res_path.exists()
    assert res_path.read_text(encoding="utf-8").startswith("# INSTITUTIONAL UNDERWRITING MEMO")


def test_plotly_chart_generators(mock_valuation_and_risk):
    """Verify all interactive Plotly charts produce valid figures."""
    _, val, risk, subsidence = mock_valuation_and_risk

    fig_waterfall = create_valuation_waterfall_chart(val)
    assert fig_waterfall is not None
    assert len(fig_waterfall.data) > 0

    fig_risk = create_risk_pillar_chart(risk)
    assert fig_risk is not None
    assert len(fig_risk.data) > 0

    fig_sub = create_subsidence_trajectory_chart(subsidence)
    assert fig_sub is not None
    assert len(fig_sub.data) == 2  # bounds envelope + central trace

    fig_comp = create_scenario_comparison_chart(val, val, "Scenario A", "Scenario B")
    assert fig_comp is not None
    assert len(fig_comp.data) == 2

    import numpy as np
    from alveris.models.multispectral_cnn import classify_parcel_zoning

    tensor = np.zeros((4, 20, 20), dtype=np.float32)
    zoning = classify_parcel_zoning(tensor, claimed_zoning="Industrial Logistics")
    fig_zoning = create_zoning_confidence_chart(zoning, claimed_zoning="Industrial Logistics")
    assert fig_zoning is not None
    assert len(fig_zoning.data) > 0
