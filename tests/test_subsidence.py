"""Unit tests for Phase 5: Vertical Land Motion & Subsidence Engine."""

import numpy as np
import pytest

from alveris.sample_data import generate_subsidence_grid_fixture
from alveris.subsidence.engine import (
    SettlementRiskLevel,
    SubsidenceModelConfig,
    analyze_parcel_subsidence,
    classify_settlement_risk,
    project_cumulative_subsidence,
)


def test_linear_vs_accelerated_subsidence_projection():
    """Verify linear and non-linear polynomial trajectory projections to 2050 and 2100."""
    # Base rate: 10 mm/year (0.01 m/year) from 2025
    rate = 10.0

    # 1. Linear model:
    # At 2050 (dt = 25 years): 10 * 25 = 250 mm = 0.25 m
    # At 2100 (dt = 75 years): 10 * 75 = 750 mm = 0.75 m
    cfg_linear = SubsidenceModelConfig(base_year=2025, model_type="linear")
    proj_2050_lin = project_cumulative_subsidence(rate, 2050, cfg_linear)
    proj_2100_lin = project_cumulative_subsidence(rate, 2100, cfg_linear)

    assert proj_2050_lin.cumulative_subsidence_m == pytest.approx(0.25, abs=1e-3)
    assert proj_2100_lin.cumulative_subsidence_m == pytest.approx(0.75, abs=1e-3)

    # 2. Accelerated model with alpha = 0.15 mm/yr²:
    # At 2050: 250 + 0.5 * 0.15 * (25^2) = 250 + 46.875 = 296.875 mm ~ 0.297 m
    # At 2100: 750 + 0.5 * 0.15 * (75^2) = 750 + 421.875 = 1171.875 mm ~ 1.172 m
    cfg_acc = SubsidenceModelConfig(
        base_year=2025, model_type="accelerated", acceleration_coeff_mm_yr2=0.15
    )
    proj_2050_acc = project_cumulative_subsidence(rate, 2050, cfg_acc)
    proj_2100_acc = project_cumulative_subsidence(rate, 2100, cfg_acc)

    assert proj_2050_acc.cumulative_subsidence_m > proj_2050_lin.cumulative_subsidence_m
    assert proj_2100_acc.cumulative_subsidence_m > proj_2100_lin.cumulative_subsidence_m
    assert proj_2050_acc.cumulative_subsidence_m == pytest.approx(0.297, abs=1e-3)
    assert proj_2100_acc.cumulative_subsidence_m == pytest.approx(1.172, abs=1e-3)


def test_differential_settlement_risk_classification():
    """Verify geotechnical threshold classification for differential ground gradient."""
    assert classify_settlement_risk(0.02) == SettlementRiskLevel.NEGLIGIBLE
    assert classify_settlement_risk(0.12) == SettlementRiskLevel.LOW
    assert classify_settlement_risk(0.35) == SettlementRiskLevel.MODERATE
    assert classify_settlement_risk(0.65) == SettlementRiskLevel.SEVERE


def test_analyze_parcel_subsidence_zonal():
    """Verify zonal statistics, span gradient, and lineage construction."""
    grid = generate_subsidence_grid_fixture((50, 50), base_rate_mm_yr=12.0)
    parcel_mask = np.zeros((50, 50), dtype=bool)
    parcel_mask[15:35, 15:35] = True  # Center 20x20 cells

    metrics = analyze_parcel_subsidence(
        subsidence_rate_grid_mm_yr=grid,
        parcel_mask=parcel_mask,
        parcel_span_meters=400.0,
    )

    assert 8.0 <= metrics.mean_subsidence_rate_mm_year <= 18.0
    assert metrics.min_subsidence_rate_mm_year <= metrics.mean_subsidence_rate_mm_year
    assert metrics.max_subsidence_rate_mm_year >= metrics.mean_subsidence_rate_mm_year
    assert metrics.differential_gradient_mm_per_m >= 0.0
    assert metrics.projection_2050.cumulative_subsidence_m > 0.0
    assert metrics.projection_2100.cumulative_subsidence_m > metrics.projection_2050.cumulative_subsidence_m
    assert metrics.lineage.feature_name == "parcel_vlm_subsidence_metrics"
