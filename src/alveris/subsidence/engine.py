"""Vertical Land Motion (VLM) and land subsidence modeling engine.

Implements Phase 5 of ALVERIS:
- InSAR / GNSS displacement rate processing (mm/year).
- Multi-decadal cumulative subsidence projections for underwriting horizons (2050, 2100).
- Linear and accelerating subsidence trajectory models:
    Linear: S(t) = rate * dt
    Accelerated: S(t) = rate * dt + 0.5 * alpha * dt^2
- Differential settlement risk index (foundation stability and soil failure proxy).
- Relative Sea-Level Rise (RSLR) coupling per IPCC AR6 Chapter 9 formulation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

from alveris.core.lineage import DerivedFeatureLineage


class SettlementRiskLevel(str, Enum):
    """Categorical rating of differential ground settlement risk."""

    NEGLIGIBLE = "negligible"
    LOW = "low"
    MODERATE = "moderate"
    SEVERE = "severe"


class SubsidenceProjection(BaseModel):
    """Cumulative vertical land motion projection for a specific future target year."""

    target_year: int = Field(..., ge=2025, le=2150, description="Future calendar year.")
    projection_model: str = Field(..., description="'linear' or 'accelerated'.")
    cumulative_subsidence_m: float = Field(
        ..., ge=0.0, description="Projected cumulative vertical drop in meters."
    )
    effective_rslr_addition_m: float = Field(
        ..., ge=0.0, description="Additive contribution to Relative Sea-Level Rise (m)."
    )


class SubsidenceMetrics(BaseModel):
    """Parcel-level vertical land motion and ground settlement metrics."""

    mean_subsidence_rate_mm_year: float = Field(
        ..., description="Average annual ground subsidence rate in mm/year (positive = sinking)."
    )
    min_subsidence_rate_mm_year: float = Field(
        ..., description="Minimum observed subsidence rate across parcel."
    )
    max_subsidence_rate_mm_year: float = Field(
        ..., description="Maximum observed subsidence rate across parcel."
    )
    differential_gradient_mm_per_m: float = Field(
        ..., description="Differential settlement gradient across parcel width (mm/meter)."
    )
    settlement_risk: SettlementRiskLevel = Field(
        ..., description="Institutional risk tier for differential ground deformation."
    )
    projection_2050: SubsidenceProjection = Field(
        ..., description="Loan horizon projection (2050)."
    )
    projection_2100: SubsidenceProjection = Field(
        ..., description="Terminal physical risk projection (2100)."
    )
    lineage: DerivedFeatureLineage = Field(
        ..., description="Provenance tracing InSAR / GNSS source and deformation models."
    )


@dataclass(frozen=True)
class SubsidenceModelConfig:
    """Configuration for subsidence trajectory simulation."""

    base_year: int = 2025
    model_type: Literal["linear", "accelerated"] = "linear"
    acceleration_coeff_mm_yr2: float = 0.15  # Additional mm/yr² under unmitigated groundwater draft


@dataclass(frozen=True)
class SubsidenceZonalStats:
    """Zonal subsidence rates and differential gradient metrics."""

    mean_rate: float
    min_rate: float
    max_rate: float
    diff_gradient: float
    risk_level: SettlementRiskLevel


def project_cumulative_subsidence(
    rate_mm_yr: float,
    target_year: int,
    config: SubsidenceModelConfig,
) -> SubsidenceProjection:
    """Project cumulative vertical displacement in meters to target year."""
    dt_years = max(0, target_year - config.base_year)
    rate_positive = max(0.0, rate_mm_yr)

    if config.model_type == "accelerated":
        sub_mm = (rate_positive * dt_years) + (
            0.5 * config.acceleration_coeff_mm_yr2 * (dt_years**2)
        )
    else:
        sub_mm = rate_positive * dt_years

    sub_meters = sub_mm / 1000.0

    return SubsidenceProjection(
        target_year=target_year,
        projection_model=config.model_type,
        cumulative_subsidence_m=round(sub_meters, 3),
        effective_rslr_addition_m=round(sub_meters, 3),
    )


def classify_settlement_risk(differential_gradient_mm_per_m: float) -> SettlementRiskLevel:
    """Classify structural foundation hazard according to geotechnical standards.

    Thresholds:
    - < 0.05 mm/m: Negligible
    - 0.05 - 0.20 mm/m: Low
    - 0.20 - 0.50 mm/m: Moderate (potential wall cracking, service utility shear)
    - > 0.50 mm/m: Severe (structural foundation compromise)
    """
    if differential_gradient_mm_per_m < 0.05:
        return SettlementRiskLevel.NEGLIGIBLE
    if differential_gradient_mm_per_m < 0.20:
        return SettlementRiskLevel.LOW
    if differential_gradient_mm_per_m < 0.50:
        return SettlementRiskLevel.MODERATE
    return SettlementRiskLevel.SEVERE


def _compute_zonal_subsidence_stats(
    rate_grid: np.ndarray, parcel_mask: np.ndarray, parcel_span_meters: float
) -> SubsidenceZonalStats:
    """Extract cell rates, mean/min/max, and calculate differential settlement gradient."""
    parcel_cells = parcel_mask & ~np.isnan(rate_grid)
    if not np.any(parcel_cells):
        rates = np.array([0.0], dtype=np.float32)
    else:
        rates = rate_grid[parcel_cells]

    mean_rate = float(np.mean(rates))
    min_rate = float(np.min(rates))
    max_rate = float(np.max(rates))

    span_m = max(10.0, parcel_span_meters)
    diff_gradient = (max_rate - min_rate) / span_m
    risk_level = classify_settlement_risk(diff_gradient)

    return SubsidenceZonalStats(
        mean_rate=mean_rate,
        min_rate=min_rate,
        max_rate=max_rate,
        diff_gradient=diff_gradient,
        risk_level=risk_level,
    )


def _build_subsidence_lineage(
    model_type: str, source_dataset_id: str
) -> DerivedFeatureLineage:
    """Build provenance record for vertical land motion analysis."""
    return DerivedFeatureLineage(
        feature_name="parcel_vlm_subsidence_metrics",
        source_dataset_ids=[source_dataset_id],
        processing_method=f"insar_time_series_{model_type}_projection",
        formula="S(t) = rate * dt [+ 0.5 * alpha * dt^2]; gradient = (max-min)/span",
        units="rates: mm/year; cumulative: meters",
        confidence=0.88,
        limitations=[
            "Assumes persistent deformation trends; does not model sudden aquifer recharge.",
            "Differential gradient measured linearly across parcel bounding diameter.",
        ],
    )


def analyze_parcel_subsidence(
    subsidence_rate_grid_mm_yr: np.ndarray,
    parcel_mask: np.ndarray,
    parcel_span_meters: float,
    config: SubsidenceModelConfig | None = None,
    source_dataset_id: str = "sentinel1_insar_displacement",
) -> SubsidenceMetrics:
    """Compute zonal ground deformation statistics and future cumulative projections."""
    cfg = config or SubsidenceModelConfig()
    stats = _compute_zonal_subsidence_stats(
        subsidence_rate_grid_mm_yr, parcel_mask, parcel_span_meters
    )

    proj_2050 = project_cumulative_subsidence(stats.mean_rate, 2050, cfg)
    proj_2100 = project_cumulative_subsidence(stats.mean_rate, 2100, cfg)
    lineage = _build_subsidence_lineage(cfg.model_type, source_dataset_id)

    return SubsidenceMetrics(
        mean_subsidence_rate_mm_year=round(stats.mean_rate, 2),
        min_subsidence_rate_mm_year=round(stats.min_rate, 2),
        max_subsidence_rate_mm_year=round(stats.max_rate, 2),
        differential_gradient_mm_per_m=round(stats.diff_gradient, 4),
        settlement_risk=stats.risk_level,
        projection_2050=proj_2050,
        projection_2100=proj_2100,
        lineage=lineage,
    )
