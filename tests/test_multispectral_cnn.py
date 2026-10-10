"""Unit tests for Multi-Spectral Deep Learning Tensor Engine."""

import numpy as np
import pytest

try:
    import torch
except (ImportError, OSError):
    torch = None

from alveris.models.multispectral_cnn import (
    LandCoverClass,
    MultiSpectralCNN,
    classify_parcel_zoning,
)


def test_cnn_architecture_forward_pass():
    """Verify PyTorch/NumPy CNN layer shapes, batch handling, and output logits."""
    model = MultiSpectralCNN(in_channels=4, num_classes=5)
    model.eval()

    if torch is not None:
        # (Batch=2, Channels=4, Height=32, Width=32)
        dummy_input = torch.randn(2, 4, 32, 32)
        with torch.no_grad():
            output = model(dummy_input)
        assert output.shape == (2, 5)
    else:
        dummy_input = np.random.randn(2, 4, 32, 32).astype(np.float32)
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

    # Spectral tensor metadata check
    bm = result.rgb_vs_multispectral_benchmark
    assert bm["input_channels"] == 4
    assert bm["red_edge_active"] is True
    assert bm["swir_absorption_active"] is True
    assert bm["dilated_convolutions"] is True

    sm = result.spectral_tensor_metadata
    assert sm["sensor"] == "Sentinel-2 Level-2A"
    assert sm["bayesian_mc_passes"] == 30
    assert "FCN-DK" in sm["spatial_dilation_mode"]

    # Lineage check
    assert result.lineage.processing_method in (
        "mc_dropout_bayesian_cnn_classification",
        "pytorch_multispectral_cnn_classification",
    )


def test_invalid_tensor_dimension_raises_error():
    """Verify error raised when tensor is not 3D (Channels, Height, Width)."""
    invalid_tensor = np.zeros((64, 64), dtype=np.float32)
    with pytest.raises(ValueError, match="Expected \\(Channels, Height, Width\\) tensor"):
        classify_parcel_zoning(
            multispectral_tensor=invalid_tensor,
            claimed_zoning="Agricultural",
        )
