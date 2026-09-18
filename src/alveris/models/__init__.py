"""Multi-spectral deep learning and computer vision models for ALVERIS."""

from alveris.models.multispectral_cnn import (
    LandCoverClass,
    MultiSpectralCNN,
    ZoningVerificationResult,
    classify_parcel_zoning,
    predict_with_bayesian_uncertainty,
)

__all__ = [
    "LandCoverClass",
    "MultiSpectralCNN",
    "ZoningVerificationResult",
    "classify_parcel_zoning",
    "predict_with_bayesian_uncertainty",
]
