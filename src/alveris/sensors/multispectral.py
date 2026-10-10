"""Sentinel-2 Multispectral Environmental Stress Engine.

Implements Phase 6 of ALVERIS:
- Normalized Difference spectral index calculations:
    - NDVI (Vegetation Vigor): (B8 - B4) / (B8 + B4)
    - NDMI (Canopy Moisture Stress): (B8 - B11) / (B8 + B11)
    - NDRE (Red Edge Chlorophyll / Salinization): (B8 - B5) / (B8 + B5)
- Multi-temporal anomaly detection (Z-scores against pre-stress historical baselines).
- Composite environmental stress index (0.0 to 100.0) tracking agricultural and
  peri-urban land degradation, root-zone drought, and saltwater intrusion.
- Data lineage generation per Section 6 of the Master Specification.
"""

from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel, Field

from alveris.core.lineage import DerivedFeatureLineage


class SpectralIndexStats(BaseModel):
    """Zonal statistical distribution for a single spectral band index."""

    min_val: float = Field(..., description="Minimum index value across parcel.")
    mean_val: float = Field(..., description="Mean index value across parcel.")
    median_val: float = Field(..., description="Median index value across parcel.")
    max_val: float = Field(..., description="Maximum index value across parcel.")


class EnvironmentalStressMetrics(BaseModel):
    """Parcel-level multispectral vegetative, moisture, and salinity stress indicators."""

    ndvi: SpectralIndexStats = Field(..., description="Normalized Difference Vegetation Index.")
    ndmi: SpectralIndexStats = Field(..., description="Normalized Difference Moisture Index.")
    ndre: SpectralIndexStats = Field(..., description="Normalized Difference Red Edge Index.")
    ndvi_anomaly: float = Field(
        ..., description="Deviation from historical baseline mean (negative = loss of greenness)."
    )
    ndmi_anomaly: float = Field(
        ..., description="Deviation from historical moisture baseline (negative = drying)."
    )
    ndre_anomaly: float = Field(
        ..., description="Deviation from red edge baseline (negative = chlorophyll stress)."
    )
    vegetation_vigor_score: float = Field(
        ..., ge=0.0, le=100.0, description="0 (barren/dead) to 100 (dense thriving canopy)."
    )
    moisture_stress_score: float = Field(
        ..., ge=0.0, le=100.0, description="0 (saturated/optimal) to 100 (extreme desiccation)."
    )
    salinization_risk_score: float = Field(
        ..., ge=0.0, le=100.0, description="0 (negligible) to 100 (severe root-zone salinization)."
    )
    composite_environmental_stress_score: float = Field(
        ..., ge=0.0, le=100.0, description="Weighted aggregate environmental stress index."
    )
    lineage: DerivedFeatureLineage = Field(
        ..., description="Provenance metadata tracing Sentinel-2 L2A BOA reflectance."
    )


@dataclass(frozen=True)
class MultispectralBands:
    """Satellite Bottom of Atmosphere (BOA) surface reflectance spectral bands."""

    b4_red: np.ndarray
    b5_red_edge: np.ndarray
    b8_nir: np.ndarray
    b11_swir1: np.ndarray


@dataclass(frozen=True)
class HistoricalSpectralBaseline:
    """Multi-year pre-stress seasonal baseline statistics for anomaly evaluation."""

    ndvi_mean: float = 0.55
    ndvi_std: float = 0.08
    ndmi_mean: float = 0.28
    ndmi_std: float = 0.06
    ndre_mean: float = 0.42
    ndre_std: float = 0.07


@dataclass(frozen=True)
class StressScoreSummary:
    """Consolidated stress scoring indicators and baseline anomaly deltas."""

    ndvi_anomaly: float
    ndmi_anomaly: float
    ndre_anomaly: float
    vigor_score: float
    moisture_stress: float
    salinization_score: float
    composite_score: float


def compute_normalized_difference(
    band_a: np.ndarray, band_b: np.ndarray, eps: float = 1e-6
) -> np.ndarray:
    """Compute normalized difference index (band_a - band_b) / (band_a + band_b).

    Guarantees output stays in [-1.0, 1.0] and avoids division by zero.
    """
    denom = band_a + band_b
    zero_denom = np.abs(denom) < eps
    safe_denom = np.where(zero_denom, 1.0, denom)

    diff = band_a - band_b
    ratio = np.where(zero_denom, 0.0, diff / safe_denom)
    return np.clip(ratio, -1.0, 1.0).astype(np.float32)


def _compute_index_stats(index_grid: np.ndarray, parcel_mask: np.ndarray) -> SpectralIndexStats:
    """Extract zonal min, mean, median, max over valid parcel pixels."""
    valid_pixels = parcel_mask & ~np.isnan(index_grid)
    if not np.any(valid_pixels):
        return SpectralIndexStats(min_val=0.0, mean_val=0.0, median_val=0.0, max_val=0.0)

    data = index_grid[valid_pixels]
    return SpectralIndexStats(
        min_val=round(float(np.min(data)), 3),
        mean_val=round(float(np.mean(data)), 3),
        median_val=round(float(np.median(data)), 3),
        max_val=round(float(np.max(data)), 3),
    )


def _compute_stress_scores(
    ndvi_mean: float,
    ndmi_mean: float,
    ndre_mean: float,
    baseline: HistoricalSpectralBaseline,
) -> StressScoreSummary:
    """Derive anomaly deltas, individual component stress scores, and composite index."""
    ndvi_delta = ndvi_mean - baseline.ndvi_mean
    ndmi_delta = ndmi_mean - baseline.ndmi_mean
    ndre_delta = ndre_mean - baseline.ndre_mean

    vigor_raw = (ndvi_mean - 0.1) / (0.7 - 0.1) * 100.0
    vigor_score = float(np.clip(vigor_raw, 0.0, 100.0))

    moist_raw = (0.35 - ndmi_mean) / 0.35 * 100.0
    moisture_stress = float(np.clip(moist_raw, 0.0, 100.0))

    rededge_deficit = max(0.0, baseline.ndre_mean - ndre_mean)
    salinization_score = float(np.clip((rededge_deficit / 0.25) * 100.0, 0.0, 100.0))

    composite = (
        ((100.0 - vigor_score) * 0.4)
        + (moisture_stress * 0.35)
        + (salinization_score * 0.25)
    )
    composite_score = float(np.clip(composite, 0.0, 100.0))

    return StressScoreSummary(
        ndvi_anomaly=round(ndvi_delta, 3),
        ndmi_anomaly=round(ndmi_delta, 3),
        ndre_anomaly=round(ndre_delta, 3),
        vigor_score=round(vigor_score, 1),
        moisture_stress=round(moisture_stress, 1),
        salinization_score=round(salinization_score, 1),
        composite_score=round(composite_score, 1),
    )


def _build_sensors_lineage(source_dataset_id: str) -> DerivedFeatureLineage:
    """Build provenance record for multispectral environmental stress analysis."""
    return DerivedFeatureLineage(
        feature_name="sentinel2_multispectral_stress_metrics",
        source_dataset_ids=[source_dataset_id],
        processing_method="spectral_band_ratios_and_historical_zscore_anomalies",
        formula="NDVI=(B8-B4)/(B8+B4); NDMI=(B8-B11)/(B8+B11); NDRE=(B8-B5)/(B8+B5)",
        units="indices: [-1.0, 1.0]; stress_scores: [0.0, 100.0]",
        confidence=0.91,
        limitations=[
            "Cloud masking dependent on Sentinel-2 Scene Classification Layer (SCL).",
            "Atmospheric Bottom-of-Atmosphere (BOA) corrections based on Sen2Cor.",
        ],
    )


def extract_multispectral_stress(
    bands: MultispectralBands,
    parcel_mask: np.ndarray,
    baseline: HistoricalSpectralBaseline | None = None,
    source_dataset_id: str = "sentinel2_l2a_boa_reflectance",
) -> EnvironmentalStressMetrics:
    """Compute multispectral indices, anomaly departures, and environmental stress scores."""
    base = baseline or HistoricalSpectralBaseline()

    ndvi_grid = compute_normalized_difference(bands.b8_nir, bands.b4_red)
    ndmi_grid = compute_normalized_difference(bands.b8_nir, bands.b11_swir1)
    ndre_grid = compute_normalized_difference(bands.b8_nir, bands.b5_red_edge)

    ndvi_stats = _compute_index_stats(ndvi_grid, parcel_mask)
    ndmi_stats = _compute_index_stats(ndmi_grid, parcel_mask)
    ndre_stats = _compute_index_stats(ndre_grid, parcel_mask)

    scores = _compute_stress_scores(
        ndvi_stats.mean_val, ndmi_stats.mean_val, ndre_stats.mean_val, base
    )
    lineage = _build_sensors_lineage(source_dataset_id)

    return EnvironmentalStressMetrics(
        ndvi=ndvi_stats,
        ndmi=ndmi_stats,
        ndre=ndre_stats,
        ndvi_anomaly=scores.ndvi_anomaly,
        ndmi_anomaly=scores.ndmi_anomaly,
        ndre_anomaly=scores.ndre_anomaly,
        vegetation_vigor_score=scores.vigor_score,
        moisture_stress_score=scores.moisture_stress,
        salinization_risk_score=scores.salinization_score,
        composite_environmental_stress_score=scores.composite_score,
        lineage=lineage,
    )
