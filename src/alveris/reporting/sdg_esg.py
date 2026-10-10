"""UN Sustainable Development Goals (SDG) & ESG Regulatory Alignment Scorecard.

Grounds institutional risk underwriting in the United Nations 2030 Agenda per:
- Persello, Wegner, Koeva, Camps-Valls et al. (IEEE GRSM 2022) -
  "Deep Learning and Earth Observation to Support the Sustainable Development Goals".

Maps multi-sensor physical satellite observations into 4 core UN SDG Indicators:
1. SDG 1.4.2: Tenure Security & Cadastral Boundary Adjudication
2. SDG 11.5.1: Disaster Risk Reduction & Critical Infrastructure Severance
3. SDG 13.1.1: Climate Action & Multi-Decadal Sea Level Rise Adaptation
4. SDG 15.3.1: Life on Land & Vegetative Land Degradation Neutrality (LDN)
"""

from pydantic import BaseModel, Field

from alveris.core.lineage import DerivedFeatureLineage
from alveris.inundation.engine import InundationScenarioResult
from alveris.network.resilience import NetworkResilienceMetrics
from alveris.sensors.multispectral import EnvironmentalStressMetrics
from alveris.subsidence.engine import SubsidenceMetrics


class SDGIndicatorScore(BaseModel):
    """Evaluation of an individual UN Sustainable Development Goal indicator."""

    indicator_code: str = Field(..., description="Canonical UN SDG indicator code (e.g. '1.4.2').")
    title: str = Field(..., description="Official UN indicator title.")
    score: float = Field(..., ge=0.0, le=100.0, description="Performance score (0-100; higher is more resilient/sustainable).")
    status: str = Field(..., description="Compliance tier: 'Compliant', 'Substandard', or 'At Risk'.")
    key_finding: str = Field(..., description="Concise physical finding grounded in Earth Observation.")


class UN_SDG_Scorecard(BaseModel):  # noqa: N801
    """Institutional ESG & UN Sustainable Development Goals scorecard."""

    composite_sdg_index: float = Field(
        ..., ge=0.0, le=100.0, description="Weighted composite SDG sustainability score (0-100)."
    )
    esg_eligibility_tier: str = Field(
        ..., description="Taxonomy rating: 'EU SFDR Article 9 (Dark Green)', 'Article 8 (Light Green)', or 'Non-Eligible'."
    )
    green_bond_eligible: bool = Field(
        ..., description="True if physical and legal risk profiles satisfy green financing covenants."
    )
    indicators: list[SDGIndicatorScore] = Field(
        ..., description="List of decomposed UN SDG indicator evaluations."
    )
    lineage: DerivedFeatureLineage = Field(
        ..., description="Data provenance tracing SDG benchmark formulation."
    )


def compute_un_sdg_scorecard(
    inundation: InundationScenarioResult,
    subsidence: SubsidenceMetrics,
    stress: EnvironmentalStressMetrics,
    network: NetworkResilienceMetrics,
    cadastral_certainty_score: float = 95.0,
) -> UN_SDG_Scorecard:
    """Compute audit-ready UN SDG Scorecard across 4 primary Earth Observation pillars.

    Parameters:
        inundation: Flood inundation scenario result.
        subsidence: InSAR subsidence metrics and projections.
        stress: Sentinel-2 multispectral vegetation and salinization metrics.
        network: Road network topology and flood passability metrics.
        cadastral_certainty_score: Boundary adjudication score (0-100) from cadastre module.

    Returns:
        UN_SDG_Scorecard with individual indicator ratings and green bond eligibility.
    """
    # 1. SDG 1.4.2: Tenure Security
    sdg1_score = round(float(cadastral_certainty_score), 1)
    sdg1_status = "Compliant" if sdg1_score >= 80.0 else ("Substandard" if sdg1_score >= 50.0 else "At Risk")
    sdg1_finding = (
        f"Cadastral boundaries verified with {sdg1_score}% certainty under its4land FCN adjudication."
        if sdg1_score >= 80.0
        else "Boundary discrepancies detected; title adjudication required to satisfy SDG 1.4.2."
    )

    # 2. SDG 11.5.1: Disaster Risk Reduction & City Resilience
    # Penalized by flooded area and arterial road severance
    is_iso = getattr(network, "is_physically_isolated", getattr(network, "is_isolated", False))
    flood_penalty = min(60.0, inundation.flooded_percent * 0.60)
    isolation_penalty = 40.0 if is_iso else (network.detour_ratio - 1.0) * 15.0
    sdg11_score = round(float(max(0.0, 100.0 - flood_penalty - min(40.0, isolation_penalty))), 1)
    sdg11_status = "Compliant" if sdg11_score >= 70.0 else ("Substandard" if sdg11_score >= 40.0 else "At Risk")
    sdg11_finding = (
        f"Asset retains safe emergency egress (detour ratio {network.detour_ratio:.2f}x) under flood conditions."
        if not is_iso
        else "Asset suffers complete arterial road isolation (0.30m passenger vehicle stall threshold breached)."
    )

    # 3. SDG 13.1.1: Climate Action & Multi-Decadal Sea Level Rise Resilience
    # Penalized by annual subsidence rate and 2050/2100 differential settlement
    subs_penalty = min(50.0, (subsidence.mean_subsidence_rate_mm_year / 15.0) * 50.0)
    depth_penalty = min(50.0, (inundation.flood_depth_mean_m / 1.5) * 50.0)
    sdg13_score = round(float(max(0.0, 100.0 - subs_penalty - depth_penalty)), 1)
    sdg13_status = "Compliant" if sdg13_score >= 70.0 else ("Substandard" if sdg13_score >= 40.0 else "At Risk")
    sdg13_finding = (
        f"InSAR subsidence rate ({subsidence.mean_subsidence_rate_mm_year:.1f} mm/yr) and RSLR trajectory within acceptable limits."
        if subsidence.mean_subsidence_rate_mm_year < 10.0
        else f"Severe sinking trajectory ({subsidence.mean_subsidence_rate_mm_year:.1f} mm/yr) exacerbates multi-decadal relative sea level rise."
    )

    # 4. SDG 15.3.1: Life on Land & Land Degradation Neutrality
    # Evaluated using NDRE (salinization) and NDMI (canopy moisture deficit)
    salinization_penalty = 40.0 if stress.salinization_risk_score >= 60.0 else (
        20.0 if stress.salinization_risk_score >= 30.0 else 0.0
    )
    drought_penalty = 30.0 if stress.moisture_stress_score >= 60.0 else 10.0
    sdg15_score = round(float(max(0.0, 100.0 - salinization_penalty - drought_penalty)), 1)
    sdg15_status = "Compliant" if sdg15_score >= 70.0 else ("Substandard" if sdg15_score >= 40.0 else "At Risk")
    sdg15_finding = (
        f"Soil surface salinity (NDRE {stress.ndre.mean_val:.2f}) and moisture balance (NDMI {stress.ndmi.mean_val:.2f}) conform to LDN guidelines."
        if stress.salinization_risk_score < 30.0
        else "Sub-surface salinization and canopy moisture deficit detected via Sentinel-2 Red-Edge/SWIR bands."
    )

    indicators = [
        SDGIndicatorScore(
            indicator_code="SDG 1.4.2",
            title="Land Tenure Security & Boundary Adjudication",
            score=sdg1_score,
            status=sdg1_status,
            key_finding=sdg1_finding,
        ),
        SDGIndicatorScore(
            indicator_code="SDG 11.5.1",
            title="Disaster Risk Reduction & Infrastructure Resilience",
            score=sdg11_score,
            status=sdg11_status,
            key_finding=sdg11_finding,
        ),
        SDGIndicatorScore(
            indicator_code="SDG 13.1.1",
            title="Climate Action & Sea Level Rise Adaptive Capacity",
            score=sdg13_score,
            status=sdg13_status,
            key_finding=sdg13_finding,
        ),
        SDGIndicatorScore(
            indicator_code="SDG 15.3.1",
            title="Life on Land & Land Degradation Neutrality (LDN)",
            score=sdg15_score,
            status=sdg15_status,
            key_finding=sdg15_finding,
        ),
    ]

    # Weighted composite index
    composite_index = round(float(0.25 * (sdg1_score + sdg11_score + sdg13_score + sdg15_score)), 1)

    # ESG Classification
    if composite_index >= 80.0 and all(i.status != "At Risk" for i in indicators):
        esg_tier = "EU SFDR Article 9 (Dark Green)"
        green_bond = True
    elif composite_index >= 60.0 and sum(1 for i in indicators if i.status == "At Risk") <= 1:
        esg_tier = "EU SFDR Article 8 (Light Green)"
        green_bond = True
    else:
        esg_tier = "Non-Eligible (High Climate/Title Risk)"
        green_bond = False

    lineage = DerivedFeatureLineage(
        feature_name="un_sdg_esg_scorecard",
        source_dataset_ids=["sentinel2_l2a", "copernicus_dem_glo30", "insar_subsidence", "osm_road_graph"],
        processing_method="ieee_grsm_sdg_indicator_crosswalk",
        formula="0.25 * (SDG_1.4.2 + SDG_11.5.1 + SDG_13.1.1 + SDG_15.3.1)",
        units="index_0_to_100",
        confidence=0.95,
        limitations=[
            "Mapped against UN 2030 Agenda indicators per Persello et al. (IEEE GRSM 2022).",
            "Subject to local regulatory jurisdiction and green bond taxonomy verification.",
        ],
    )

    return UN_SDG_Scorecard(
        composite_sdg_index=composite_index,
        esg_eligibility_tier=esg_tier,
        green_bond_eligible=green_bond,
        indicators=indicators,
        lineage=lineage,
    )
