"""Risk scoring, component decomposition, and explainability module for ALVERIS."""

from alveris.risk.scoring import (
    ComponentRiskScores,
    CompositeRiskAssessment,
    RiskTier,
    RiskWeightsConfig,
    classify_risk_tier,
    compute_inundation_score,
    compute_network_score,
    compute_subsidence_score,
    evaluate_composite_risk,
)

__all__ = [
    "ComponentRiskScores",
    "CompositeRiskAssessment",
    "RiskTier",
    "RiskWeightsConfig",
    "classify_risk_tier",
    "compute_inundation_score",
    "compute_network_score",
    "compute_subsidence_score",
    "evaluate_composite_risk",
]
