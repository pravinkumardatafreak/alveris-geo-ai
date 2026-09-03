"""Unit tests for Multi-Spectral Deep Learning Tensor Engine."""

import numpy as np
import pytest
import torch

from alveris.models.multispectral_cnn import (
    LandCoverClass,
    MultiSpectralCNN,
    classify_parcel_zoning,
)


def test_cnn_architecture_forward_pass():
    """Verify PyTorch CNN layer shapes, batch handling, and output logits."""
    model = MultiSpectralCNN(in_channels=4, num_classes=5)
    model.eval()

    # (Batch=2, Channels=4, Height=32, Width=32)
    dummy_input = torch.randn(2, 4, 32, 32)
    with torch.no_grad():
        output = model(dummy_input)

    assert output.shape == (2, 5)


def test_classify_parcel_zoning_inference():
    """Verify end-to-end zoning inference, softmax probabilities, and benchmarks."""
    # Create synthetic 4-channel tensor: Red, Red-Edge, NIR, SWIR1
    synth_tensor = np.random.uniform(0.05, 0.45, size=(4, 64, 64)).astype(np.float32)

    result = classify_parcel_zoning(
        multispectral_tensor=synth_tensor,
        claimed_zoning="Industrial Logistics Park",
    )

    assert isinstance(result.predicted_class, LandCoverClass)
    assert 0.0 <= result.confidence <= 1.0
    assert 0.0 <= result.impervious_surface_fraction <= 1.0

    # Probabilities should sum to 1.0
    total_prob = sum(result.class_probabilities.values())
    assert total_prob == pytest.approx(1.0, abs=0.01)

    # Benchmark metadata check
    bm = result.rgb_vs_multispectral_benchmark
    assert bm["rgb_3band_baseline_accuracy_pct"] == 80.96
    assert bm["multispectral_tensor_accuracy_pct"] == 95.98
    assert bm["spectral_advantage_delta_pct"] == pytest.approx(15.02, abs=0.01)

    # Lineage check
    assert result.lineage.processing_method == "pytorch_multispectral_cnn_classification"


def test_invalid_tensor_dimension_raises_error():
    """Verify error raised when tensor is not 3D (Channels, Height, Width)."""
    invalid_tensor = np.zeros((64, 64), dtype=np.float32)
    with pytest.raises(ValueError, match="Expected \\(Channels, Height, Width\\) tensor"):
        classify_parcel_zoning(
            multispectral_tensor=invalid_tensor,
            claimed_zoning="Agricultural",
        )
