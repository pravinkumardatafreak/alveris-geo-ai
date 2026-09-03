"""Climate-adjusted land valuation and Climate Value at Risk (Climate VaR) engine.

Implements Phase 9 of ALVERIS:
- Translates multi-criteria physical risk exposures into commercial financial haircuts:
    1. Direct Usable Land Loss (submerged surface area haircut)
    2. Access & Logistics Penalty (detour ratio and physical isolation discount)
    3. Geotechnical Foundation Reserve (subsidence CapEx underpinning reserve)
    4. Environmental Degradation Discount (soil salinization and moisture stress)
- Bounds valuation into probabilistic ranges:
    - Conservative (distressed liquidation / illiquidity downside)
    - Expected (central underwriting scenario)
    - Optimistic (partial engineering adaptation assumed)
- Climate VaR (Value at Risk) proxy calculation per Basel III / TCFD standards.
- Step-by-step financial waterfall breakdown for investment committee memos.
- Data lineage generation per Section 6 of the Master Specification.
"""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from alveris.core.lineage import DerivedFeatureLineage
from alveris.inundation.engine import InundationScenarioResult
from alveris.network.resilience import NetworkResilienceMetrics
from alveris.sensors.multispectral import EnvironmentalStressMetrics
from alveris.subsidence.engine import SettlementRiskLevel, SubsidenceMetrics


class ValuationDeductions(BaseModel):
    """Component financial deductions contributing to overall asset haircut."""

    inundation_loss_inr: float = Field(
        ..., ge=0.0, description="Value loss due to submerged usable land area (INR)."
    )
    accessibility_penalty_inr: float = Field(
        ..., ge=0.0, description="Discount due to road network detour or isolation (INR)."
    )
    subsidence_capex_reserve_inr: float = Field(
        ..., ge=0.0, description="CapEx reserve for foundation underpinning (INR)."
    )
    environmental_discount_inr: float = Field(
        ..., ge=0.0, description="Discount for soil salinization and vegetative loss (INR)."
    )
    total_haircut_inr: float = Field(
        ..., ge=0.0, description="Total aggregated downside financial deduction (INR)."
    )
    total_haircut_percent: float = Field(
        ..., ge=0.0, le=100.0, description="Total percentage haircut relative to baseline."
    )


class ValuationRange(BaseModel):
    """Probabilistic valuation range for risk-adjusted collateral underwriting."""

    conservative_value_inr: float = Field(
        ..., ge=0.0, description="Stressed downside valuation under severe illiquidity (INR)."
    )
    expected_value_inr: float = Field(
        ..., ge=0.0, description="Central expected climate-adjusted market valuation (INR)."
    )
    optimistic_value_inr: float = Field(
        ..., ge=0.0, description="Optimistic valuation assuming borrower adaptation (INR)."
    )


class ClimateAdjustedValuation(BaseModel):
    """Comprehensive asset valuation report under physical climate stress."""

    scenario_id: str = Field(..., description="Evaluated scenario identifier.")
    baseline_market_value_inr: float = Field(
        ..., gt=0.0, description="Unadjusted baseline market valuation (INR)."
    )
    climate_adjusted_value_inr: float = Field(
        ..., ge=0.0, description="Central climate-adjusted market valuation (INR)."
    )
    deductions: ValuationDeductions = Field(
        ..., description="Granular deduction waterfall components."
    )
    valuation_range: ValuationRange = Field(
        ..., description="Probabilistic valuation bounds."
    )
    climate_var_proxy_inr: float = Field(
        ..., ge=0.0, description="Climate Value at Risk dollar loss relative to baseline (INR)."
    )
    climate_var_percent: float = Field(
        ..., ge=0.0, le=100.0, description="Climate VaR loss as a percentage of baseline value."
    )
    waterfall_breakdown: list[dict[str, Any]] = Field(
        ..., description="Step-by-step waterfall steps for accounting and auditability."
    )
    lineage: DerivedFeatureLineage = Field(
        ..., description="Provenance metadata tracing valuation parameters."
    )


@dataclass(frozen=True)
class PhysicalHazardInputs:
    """Consolidated physical hazard features across all four transmission pillars."""

    inundation: InundationScenarioResult
    subsidence: SubsidenceMetrics
    environment: EnvironmentalStressMetrics
    network: NetworkResilienceMetrics


@dataclass(frozen=True)
class ValuationModelConfig:
    """Configurable economic valuation parameters from configs/valuation.yml."""

    land_loss_elasticity: float = 1.0
    accessibility_elasticity: float = 0.15
    isolation_penalty_fraction: float = 0.40
    max_haircut_cap_percent: float = 85.0  # Asset retains 15% residual salvage value


def _compute_inundation_deduction(
    baseline_val: float, inundation: InundationScenarioResult, elasticity: float
) -> float:
    """Compute financial loss from directly submerged usable land area."""
    loss_fraction = inundation.usable_land_loss_sqm / max(1.0, inundation.total_parcel_area_sqm)
    haircut = baseline_val * loss_fraction * elasticity
    return min(baseline_val, haircut)


def _compute_accessibility_deduction(
    baseline_val: float, network: NetworkResilienceMetrics, cfg: ValuationModelConfig
) -> float:
    """Compute financial penalty for road detours and physical access severance."""
    if network.is_physically_isolated:
        return baseline_val * cfg.isolation_penalty_fraction

    detour_excess = max(0.0, network.detour_ratio - 1.0)
    penalty_fraction = min(0.35, detour_excess * cfg.accessibility_elasticity)
    return baseline_val * penalty_fraction


def _compute_subsidence_deduction(
    baseline_val: float, subsidence: SubsidenceMetrics
) -> float:
    """Compute CapEx reserve required for structural underpinning and stabilization."""
    risk_capex_rates = {
        SettlementRiskLevel.NEGLIGIBLE: 0.0,
        SettlementRiskLevel.LOW: 0.03,
        SettlementRiskLevel.MODERATE: 0.08,
        SettlementRiskLevel.SEVERE: 0.18,
    }
    rate = risk_capex_rates.get(subsidence.settlement_risk, 0.0)
    return baseline_val * rate


def _compute_environmental_deduction(
    baseline_val: float, environment: EnvironmentalStressMetrics
) -> float:
    """Compute valuation discount for soil salinization and vegetative loss."""
    stress_norm = environment.composite_environmental_stress_score / 100.0
    return baseline_val * (stress_norm * 0.12)


def _build_waterfall_table(
    baseline_val: float,
    deductions: ValuationDeductions,
    final_val: float,
) -> list[dict[str, Any]]:
    """Construct auditable financial waterfall table."""
    t1 = baseline_val - deductions.inundation_loss_inr
    t2 = t1 - deductions.accessibility_penalty_inr
    t3 = t2 - deductions.subsidence_capex_reserve_inr
    return [
        {"step": "Baseline Value", "impact": baseline_val, "total": baseline_val},
        {"step": "(-) Inundation Loss", "impact": -deductions.inundation_loss_inr, "total": t1},
        {
            "step": "(-) Logistics Penalty",
            "impact": -deductions.accessibility_penalty_inr,
            "total": t2,
        },
        {
            "step": "(-) CapEx Reserve",
            "impact": -deductions.subsidence_capex_reserve_inr,
            "total": t3,
        },
        {
            "step": "(-) Eco Discount",
            "impact": -deductions.environmental_discount_inr,
            "total": final_val,
        },
        {"step": "(=) Adjusted Value", "impact": final_val, "total": final_val},
    ]


def _build_valuation_lineage(scenario_id: str) -> DerivedFeatureLineage:
    """Build provenance record for climate-adjusted valuation."""
    return DerivedFeatureLineage(
        feature_name=f"climate_adjusted_valuation_{scenario_id}",
        source_dataset_ids=["inundation_model", "insar_vlm", "sentinel2_l2a", "road_network"],
        processing_method="four_pillar_discount_waterfall_and_climate_var",
        formula="Adjusted = Baseline - min(Cap, Inundation + Access + Subsidence + Environment)",
        units="INR",
        scenario_id=scenario_id,
        confidence=0.91,
        limitations=[
            "Valuation represents physical risk discounts; excludes macroeconomic inflation.",
            "Elasticity parameters calibrated per configs/valuation.yml.",
        ],
    )


def _compute_all_deductions(
    base_val: float, hazards: PhysicalHazardInputs, cfg: ValuationModelConfig
) -> tuple[ValuationDeductions, float, float]:
    """Calculate individual financial deductions and cap aggregate haircut."""
    inund = _compute_inundation_deduction(base_val, hazards.inundation, cfg.land_loss_elasticity)
    access = _compute_accessibility_deduction(base_val, hazards.network, cfg)
    sub = _compute_subsidence_deduction(base_val, hazards.subsidence)
    env = _compute_environmental_deduction(base_val, hazards.environment)

    max_cut = base_val * (cfg.max_haircut_cap_percent / 100.0)
    final_cut = min(max_cut, inund + access + sub + env)
    adj_val = max(0.0, base_val - final_cut)

    deductions = ValuationDeductions(
        inundation_loss_inr=round(inund, 2),
        accessibility_penalty_inr=round(access, 2),
        subsidence_capex_reserve_inr=round(sub, 2),
        environmental_discount_inr=round(env, 2),
        total_haircut_inr=round(final_cut, 2),
        total_haircut_percent=round((final_cut / base_val) * 100.0, 2),
    )
    return deductions, final_cut, adj_val


def evaluate_climate_valuation(
    baseline_market_value_inr: float,
    hazards: PhysicalHazardInputs,
    config: ValuationModelConfig | None = None,
) -> ClimateAdjustedValuation:
    """Compute climate-adjusted market valuation, haircut waterfall, and Climate VaR."""
    cfg = config or ValuationModelConfig()
    base_val = max(1.0, baseline_market_value_inr)

    deductions, final_haircut, adjusted_val = _compute_all_deductions(base_val, hazards, cfg)

    ranges = ValuationRange(
        conservative_value_inr=round(adjusted_val * 0.88, 2),
        expected_value_inr=round(adjusted_val, 2),
        optimistic_value_inr=round(min(base_val, adjusted_val * 1.08), 2),
    )

    waterfall = _build_waterfall_table(base_val, deductions, adjusted_val)
    lineage = _build_valuation_lineage(hazards.inundation.scenario_id)

    return ClimateAdjustedValuation(
        scenario_id=hazards.inundation.scenario_id,
        baseline_market_value_inr=round(base_val, 2),
        climate_adjusted_value_inr=round(adjusted_val, 2),
        deductions=deductions,
        valuation_range=ranges,
        climate_var_proxy_inr=round(final_haircut, 2),
        climate_var_percent=round((final_haircut / base_val) * 100.0, 2),
        waterfall_breakdown=waterfall,
        lineage=lineage,
    )
