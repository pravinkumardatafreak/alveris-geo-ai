"""Interactive Plotly chart generation module for ALVERIS.

Provides presentation-grade interactive charts for institutional investment
committees, bank credit officers, and real estate valuation leads.
"""

from typing import Any

import plotly.graph_objects as go

from alveris.models.multispectral_cnn import ZoningVerificationResult
from alveris.risk.scoring import CompositeRiskAssessment
from alveris.subsidence.engine import SubsidenceMetrics
from alveris.valuation.engine import ClimateAdjustedValuation

DARK_THEME_LAYOUT: dict[str, Any] = {
    "paper_bgcolor": "#0f172a",
    "plot_bgcolor": "#0f172a",
    "font": {"color": "#e2e8f0", "family": "Inter, Segoe UI, sans-serif"},
    "margin": {"l": 40, "r": 40, "t": 50, "b": 40},
    "xaxis": {"gridcolor": "#1e293b", "zerolinecolor": "#334155"},
    "yaxis": {"gridcolor": "#1e293b", "zerolinecolor": "#334155"},
}


def create_valuation_waterfall_chart(valuation: ClimateAdjustedValuation) -> go.Figure:
    """Create interactive financial waterfall chart from baseline to adjusted value."""
    base = valuation.baseline_market_value_inr
    d = valuation.deductions

    steps = [
        "Baseline Value",
        "Usable Land Loss",
        "Logistics Severance",
        "Subsidence CapEx",
        "Environmental Discount",
        "Climate Adjusted Value",
    ]
    measures = ["absolute", "relative", "relative", "relative", "relative", "total"]
    y_values = [
        base,
        -d.inundation_loss_inr,
        -d.accessibility_penalty_inr,
        -d.subsidence_capex_reserve_inr,
        -d.environmental_discount_inr,
        0.0,
    ]
    text_labels = [
        f"₹{base / 1e6:.2f}M",
        f"-₹{d.inundation_loss_inr / 1e6:.2f}M" if d.inundation_loss_inr > 0 else "₹0",
        f"-₹{d.accessibility_penalty_inr / 1e6:.2f}M" if d.accessibility_penalty_inr > 0 else "₹0",
        f"-₹{d.subsidence_capex_reserve_inr / 1e6:.2f}M"
        if d.subsidence_capex_reserve_inr > 0
        else "₹0",
        f"-₹{d.environmental_discount_inr / 1e6:.2f}M"
        if d.environmental_discount_inr > 0
        else "₹0",
        f"₹{valuation.climate_adjusted_value_inr / 1e6:.2f}M",
    ]

    fig = go.Figure(
        go.Waterfall(
            name="Valuation",
            orientation="v",
            measure=measures,
            x=steps,
            textposition="outside",
            text=text_labels,
            y=y_values,
            connector={"line": {"color": "#64748b"}},
            decreasing={"marker": {"color": "#ef4444"}},
            increasing={"marker": {"color": "#10b981"}},
            totals={"marker": {"color": "#3b82f6"}},
        )
    )

    fig.update_layout(
        title={"text": "<b>Underwriting Haircut Waterfall (INR)</b>", "x": 0.05},
        yaxis_title="Asset Value (INR)",
        **DARK_THEME_LAYOUT,
    )
    return fig


def create_zoning_confidence_chart(
    zoning: ZoningVerificationResult, claimed_zoning: str
) -> go.Figure:
    """Create horizontal bar chart of PyTorch multi-spectral CNN class probabilities."""
    sorted_probs = sorted(
        zoning.class_probabilities.items(), key=lambda x: x[1], reverse=False
    )
    labels = [k.replace("_", " ").title() for k, _ in sorted_probs]
    scores = [v * 100.0 for _, v in sorted_probs]

    colors = []
    for k, _ in sorted_probs:
        if k == zoning.predicted_class.value:
            colors.append("#10b981")  # Predicted top class
        elif claimed_zoning.lower() in k.lower():
            colors.append("#38bdf8")  # Claimed class match
        else:
            colors.append("#475569")

    fig = go.Figure(
        go.Bar(
            x=scores,
            y=labels,
            orientation="h",
            marker={"color": colors},
            text=[f"{s:.1f}%" for s in scores],
            textposition="inside",
        )
    )
    fig.update_layout(
        title={
            "text": "<b>Multi-Spectral CNN Land Cover Verification (13-Band Tensor)</b>",
            "x": 0.05,
        },
        xaxis_title="Classification Probability (%)",
        xaxis_range=[0, 100],
        **DARK_THEME_LAYOUT,
    )
    return fig


def create_scenario_comparison_chart(
    val_a: ClimateAdjustedValuation,
    val_b: ClimateAdjustedValuation,
    label_a: str,
    label_b: str,
) -> go.Figure:
    """Create grouped bar chart comparing transmission deductions across two scenarios."""
    categories = [
        "Inundation Land Loss",
        "Logistics Severance",
        "Subsidence CapEx",
        "Environmental Discount",
        "Total Haircut",
    ]
    vals_a = [
        val_a.deductions.inundation_loss_inr / 1e6,
        val_a.deductions.accessibility_penalty_inr / 1e6,
        val_a.deductions.subsidence_capex_reserve_inr / 1e6,
        val_a.deductions.environmental_discount_inr / 1e6,
        val_a.deductions.total_haircut_inr / 1e6,
    ]
    vals_b = [
        val_b.deductions.inundation_loss_inr / 1e6,
        val_b.deductions.accessibility_penalty_inr / 1e6,
        val_b.deductions.subsidence_capex_reserve_inr / 1e6,
        val_b.deductions.environmental_discount_inr / 1e6,
        val_b.deductions.total_haircut_inr / 1e6,
    ]

    fig = go.Figure(
        data=[
            go.Bar(name=label_a, x=categories, y=vals_a, marker={"color": "#38bdf8"}),
            go.Bar(name=label_b, x=categories, y=vals_b, marker={"color": "#f43f5e"}),
        ]
    )
    fig.update_layout(
        barmode="group",
        title={
            "text": "<b>Cross-Scenario Haircut Comparison by Transmission Channel</b>",
            "x": 0.05,
        },
        yaxis_title="Deduction (INR Millions)",
        legend={"orientation": "h", "y": 1.1, "x": 0.05},
        **DARK_THEME_LAYOUT,
    )
    return fig


def create_subsidence_trajectory_chart(subsidence: SubsidenceMetrics) -> go.Figure:
    """Create time-series subsidence projection chart with uncertainty bounds."""
    rate_m_yr = subsidence.mean_subsidence_rate_mm_year / 1000.0
    years = [2025, 2035, 2050, 2075, 2100]

    central_m = [(yr - 2025) * rate_m_yr for yr in years]
    upper_m = [c * 1.30 for c in central_m]
    lower_m = [c * 0.70 for c in central_m]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years + years[::-1],
            y=upper_m + lower_m[::-1],
            fill="toself",
            fillcolor="rgba(244, 63, 94, 0.15)",
            line={"color": "rgba(255,255,255,0)"},
            hoverinfo="skip",
            showlegend=True,
            name="±30% Geotechnical Bounds",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=central_m,
            mode="lines+markers",
            line={"color": "#f43f5e", "width": 3},
            name="Expected Sinking (Linear InSAR)",
        )
    )

    fig.update_layout(
        title={
            "text": "<b>Multi-Decadal InSAR Ground Subsidence Trajectory (2025–2100)</b>",
            "x": 0.05,
        },
        xaxis_title="Horizon Year",
        yaxis_title="Cumulative Subsidence (Meters)",
        **DARK_THEME_LAYOUT,
    )
    return fig


def create_risk_pillar_chart(risk: CompositeRiskAssessment) -> go.Figure:
    """Create horizontal bar chart of the four physical risk pillars."""
    comp = risk.components
    labels = [
        "Inundation Hazard (40% wt)",
        "Subsidence Hazard (20% wt)",
        "Environmental Stress (20% wt)",
        "Network Disruption (20% wt)",
    ]
    scores = [
        comp.inundation_hazard_score,
        comp.subsidence_hazard_score,
        comp.environmental_stress_score,
        comp.network_disruption_score,
    ]

    colors = []
    for s in scores:
        if s >= 70:
            colors.append("#ef4444")
        elif s >= 45:
            colors.append("#f59e0b")
        else:
            colors.append("#10b981")

    fig = go.Figure(
        go.Bar(
            x=scores,
            y=labels,
            orientation="h",
            marker={"color": colors},
            text=[f"{s:.1f} / 100" for s in scores],
            textposition="inside",
        )
    )
    score_str = f"{risk.composite_risk_score:.1f}/100"
    fig.update_layout(
        title={
            "text": f"<b>Four-Pillar Risk Scores (Composite: {score_str})</b>",
            "x": 0.05,
        },
        xaxis_title="Hazard Score (0-100)",
        xaxis_range=[0, 100],
        **DARK_THEME_LAYOUT,
    )
    return fig
