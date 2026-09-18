"""Tests for Monte Carlo Dropout Bayesian Uncertainty and OOD Detection."""

import numpy as np

try:
    import torch
except (ImportError, OSError):
    torch = None

from alveris.models.multispectral_cnn import (
    MultiSpectralCNN,
    ZoningVerificationResult,
    classify_parcel_zoning,
    predict_with_bayesian_uncertainty,
)


def test_multispectral_cnn_dropout_layers():
    """Verify that MultiSpectralCNN initializes with Spatial & Linear Dropout or fallback weights."""
    model = MultiSpectralCNN(in_channels=4, num_classes=5, dropout_p=0.25)
    assert model.dropout_p == 0.25

    if torch is not None and hasattr(model, "features"):
        # Verify dropout layers exist in features and classifier
        dropout2d_count = sum(1 for m in model.features if isinstance(m, torch.nn.Dropout2d))
        dropout_count = sum(1 for m in model.classifier if isinstance(m, torch.nn.Dropout))
        assert dropout2d_count >= 2
        assert dropout_count >= 1
    else:
        assert hasattr(model, "w_proj")


def test_predict_with_bayesian_uncertainty_bounds():
    """Verify Monte Carlo Dropout produces valid probability distribution and uncertainty metrics."""
    model = MultiSpectralCNN(in_channels=4, num_classes=5, dropout_p=0.20)
    # Synthetic 4-channel tensor: (4, 32, 32)
    np.random.seed(42)
    tensor = np.random.uniform(0.05, 0.45, size=(4, 32, 32)).astype(np.float32)

    mean_probs, epistemic_var, aleatoric_ent, is_ood = predict_with_bayesian_uncertainty(
        model=model,
        tensor_np=tensor,
        n_forward_passes=20,
        ood_variance_threshold=0.030,
    )

    # Probabilities must sum to ~1.0
    assert mean_probs.shape == (5,)
    assert np.isclose(np.sum(mean_probs), 1.0, atol=1e-4)
    assert np.all(mean_probs >= 0.0)

    # Uncertainty metrics must be non-negative
    assert epistemic_var >= 0.0
    assert aleatoric_ent >= 0.0
    assert isinstance(is_ood, (bool, np.bool_))


def test_classify_parcel_zoning_bayesian_integration():
    """Verify classify_parcel_zoning returns populated Bayesian uncertainty fields."""
    tensor = np.random.uniform(0.1, 0.4, size=(13, 32, 32)).astype(np.float32)
    res = classify_parcel_zoning(
        multispectral_tensor=tensor,
        claimed_zoning="Coastal Logistics & Industrial Park",
        enable_bayesian_uncertainty=True,
    )

    assert isinstance(res, ZoningVerificationResult)
    assert res.epistemic_uncertainty >= 0.0
    assert res.aleatoric_uncertainty >= 0.0
    assert res.uncertainty_rating in [
        "High Confidence",
        "Moderate Uncertainty",
        "Out-of-Distribution (OOD)",
    ]
    assert "mc_dropout_bayesian_cnn_classification" in res.lineage.processing_method
