"""Unit tests for Phase 6: Sentinel-2 Multispectral Environmental Stress Engine."""

import numpy as np
import pytest

from alveris.sample_data import generate_sentinel2_bands_fixture
from alveris.sensors.multispectral import (
    HistoricalSpectralBaseline,
    MultispectralBands,
    compute_normalized_difference,
    extract_multispectral_stress,
)


def test_normalized_difference_math_and_clipping():
    """Verify normalized difference calculation, zero handling, and bounds [-1, 1]."""
    # Simple known inputs: A = 0.6, B = 0.2 -> (0.6 - 0.2) / (0.6 + 0.2) = 0.4 / 0.8 = 0.5
    a = np.array([[0.6]], dtype=np.float32)
    b = np.array([[0.2]], dtype=np.float32)
    res = compute_normalized_difference(a, b)
    assert res[0, 0] == pytest.approx(0.5, abs=1e-4)

    # Division by zero: A = 0, B = 0 -> should output 0.0 without warning
    z_a = np.array([[0.0]], dtype=np.float32)
    z_b = np.array([[0.0]], dtype=np.float32)
    z_res = compute_normalized_difference(z_a, z_b)
    assert z_res[0, 0] == 0.0

    # Strong inverted ratio: A = 0.1, B = 0.9 -> (0.1 - 0.9) / 1.0 = -0.8
    inv_a = np.array([[0.1]], dtype=np.float32)
    inv_b = np.array([[0.9]], dtype=np.float32)
    inv_res = compute_normalized_difference(inv_a, inv_b)
    assert inv_res[0, 0] == pytest.approx(-0.8, abs=1e-4)


def test_healthy_vs_stressed_canopy_metrics():
    """Verify environmental stress differentiation between healthy vs degraded parcel."""
    grid_shape = (40, 40)
    parcel_mask = np.zeros(grid_shape, dtype=bool)
    parcel_mask[10:30, 10:30] = True  # Central 20x20 parcel

    baseline = HistoricalSpectralBaseline(
        ndvi_mean=0.55, ndmi_mean=0.28, ndre_mean=0.42
    )

    # 1. Healthy canopy
    h_b4, h_b5, h_b8, h_b11 = generate_sentinel2_bands_fixture(grid_shape, condition="healthy")
    healthy_bands = MultispectralBands(b4_red=h_b4, b5_red_edge=h_b5, b8_nir=h_b8, b11_swir1=h_b11)
    healthy_metrics = extract_multispectral_stress(
        bands=healthy_bands,
        parcel_mask=parcel_mask,
        baseline=baseline,
    )

    # 2. Stressed / salinized canopy
    s_b4, s_b5, s_b8, s_b11 = generate_sentinel2_bands_fixture(grid_shape, condition="stressed")
    stressed_bands = MultispectralBands(b4_red=s_b4, b5_red_edge=s_b5, b8_nir=s_b8, b11_swir1=s_b11)
    stressed_metrics = extract_multispectral_stress(
        bands=stressed_bands,
        parcel_mask=parcel_mask,
        baseline=baseline,
    )

    # Healthy parcel: High NDVI, high vigor, low moisture stress, low composite stress
    assert healthy_metrics.ndvi.mean_val > 0.65
    assert healthy_metrics.vegetation_vigor_score > 80.0
    assert healthy_metrics.moisture_stress_score < 25.0
    assert healthy_metrics.composite_environmental_stress_score < 30.0

    # Stressed parcel: Low NDVI, low vigor, high moisture & composite stress
    assert stressed_metrics.ndvi.mean_val < 0.25
    assert stressed_metrics.vegetation_vigor_score < 30.0
    assert stressed_metrics.moisture_stress_score > 70.0
    assert stressed_metrics.composite_environmental_stress_score > 60.0

    # Anomaly checks: healthy has positive anomaly, stressed has negative anomaly
    assert healthy_metrics.ndvi_anomaly > 0.0
    assert stressed_metrics.ndvi_anomaly < 0.0
    assert stressed_metrics.ndmi_anomaly < 0.0

    # Lineage check
    assert healthy_metrics.lineage.feature_name == "sentinel2_multispectral_stress_metrics"
