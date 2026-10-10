import React from 'react';
import {
  ClimateAdjustedValuation,
  CompositeRiskAssessment,
  SubsidenceMetrics,
  ZoningVerificationResult,
} from '../engine/alverisEngine';

/**
 * Interactive SVG Valuation Waterfall Chart matching `create_valuation_waterfall_chart` in `charts.py`
 */
export const ValuationWaterfallChart: React.FC<{ valuation: ClimateAdjustedValuation }> = ({
  valuation,
}) => {
  const base = valuation.baseline_market_value_inr;
  const d = valuation.deductions;
  const adj = valuation.climate_adjusted_value_inr;

  const steps = [
    {
      label: 'Baseline Value',
      shortLabel: 'Baseline',
      start: 0,
      end: base,
      delta: base,
      color: '#10b981',
      text: `₹${(base / 1e6).toFixed(2)}M`,
    },
    {
      label: 'Usable Land Loss',
      shortLabel: 'Inundation',
      start: base,
      end: base - d.inundation_loss_inr,
      delta: -d.inundation_loss_inr,
      color: '#ef4444',
      text: d.inundation_loss_inr > 0 ? `-₹${(d.inundation_loss_inr / 1e6).toFixed(2)}M` : '₹0',
    },
    {
      label: 'Logistics Severance',
      shortLabel: 'Logistics',
      start: base - d.inundation_loss_inr,
      end: base - d.inundation_loss_inr - d.accessibility_penalty_inr,
      delta: -d.accessibility_penalty_inr,
      color: '#ef4444',
      text:
        d.accessibility_penalty_inr > 0
          ? `-₹${(d.accessibility_penalty_inr / 1e6).toFixed(2)}M`
          : '₹0',
    },
    {
      label: 'Subsidence CapEx',
      shortLabel: 'Subsidence',
      start: base - d.inundation_loss_inr - d.accessibility_penalty_inr,
      end:
        base -
        d.inundation_loss_inr -
        d.accessibility_penalty_inr -
        d.subsidence_capex_reserve_inr,
      delta: -d.subsidence_capex_reserve_inr,
      color: '#ef4444',
      text:
        d.subsidence_capex_reserve_inr > 0
          ? `-₹${(d.subsidence_capex_reserve_inr / 1e6).toFixed(2)}M`
          : '₹0',
    },
    {
      label: 'Environmental Discount',
      shortLabel: 'Eco Stress',
      start:
        base -
        d.inundation_loss_inr -
        d.accessibility_penalty_inr -
        d.subsidence_capex_reserve_inr,
      end: adj,
      delta: -d.environmental_discount_inr,
      color: '#ef4444',
      text:
        d.environmental_discount_inr > 0
          ? `-₹${(d.environmental_discount_inr / 1e6).toFixed(2)}M`
          : '₹0',
    },
    {
      label: 'Climate Adjusted Value',
      shortLabel: 'Adjusted',
      start: 0,
      end: adj,
      delta: adj,
      color: '#3b82f6',
      text: `₹${(adj / 1e6).toFixed(2)}M`,
    },
  ];

  const maxY = Math.max(base * 1.15, 1);
  const chartHeight = 220;
  const yPos = (val: number) => chartHeight - (Math.max(0, val) / maxY) * chartHeight + 30;

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4 h-full flex flex-col justify-between">
      <div className="font-bold text-slate-100 text-sm mb-2">
        Underwriting Haircut Waterfall (INR)
      </div>
      <svg viewBox="0 0 620 295" className="w-full h-auto select-none">
        {/* Horizontal Grid Lines */}
        {[0, 0.25, 0.5, 0.75, 1.0].map((frac) => {
          const val = base * frac;
          const y = yPos(val);
          return (
            <g key={frac}>
              <line x1={55} y1={y} x2={600} y2={y} stroke="#1e293b" strokeWidth={1} />
              <text x={50} y={y + 4} textAnchor="end" fill="#94a3b8" fontSize="10">
                ₹{(val / 1e6).toFixed(1)}M
              </text>
            </g>
          );
        })}

        {steps.map((s, idx) => {
          const x = 75 + idx * 86;
          const barW = 52;
          const topVal = Math.max(s.start, s.end);
          const botVal = Math.min(s.start, s.end);
          const yTop = yPos(topVal);
          const yBot = yPos(botVal);
          const h = Math.max(3, yBot - yTop);
          const nextStep = steps[idx + 1];

          return (
            <g key={s.label}>
              {nextStep && (
                <line
                  x1={x + barW}
                  y1={yPos(s.end)}
                  x2={x + 86}
                  y2={yPos(s.end)}
                  stroke="#64748b"
                  strokeDasharray="3,3"
                  strokeWidth={1.2}
                />
              )}
              <rect
                x={x}
                y={yTop}
                width={barW}
                height={h}
                fill={s.color}
                rx={3}
                className="transition-all duration-300"
              />
              <text
                x={x + barW / 2}
                y={yTop - 6}
                textAnchor="middle"
                fill="#e2e8f0"
                fontSize="10"
                fontWeight="600"
              >
                {s.text}
              </text>
              <text
                x={x + barW / 2}
                y={272}
                textAnchor="middle"
                fill="#cbd5e1"
                fontSize="10"
              >
                {s.shortLabel}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

/**
 * Four-Pillar Risk Scores Horizontal Bar Chart matching `create_risk_pillar_chart`
 */
export const RiskPillarChart: React.FC<{ risk: CompositeRiskAssessment }> = ({ risk }) => {
  const pillars = [
    {
      label: 'Inundation Hazard (40% wt)',
      score: risk.components.inundation_hazard_score,
    },
    {
      label: 'Subsidence Hazard (20% wt)',
      score: risk.components.subsidence_hazard_score,
    },
    {
      label: 'Environmental Stress (20% wt)',
      score: risk.components.environmental_stress_score,
    },
    {
      label: 'Network Disruption (20% wt)',
      score: risk.components.network_disruption_score,
    },
  ];

  const getColor = (s: number) => {
    if (s >= 70) return '#ef4444';
    if (s >= 45) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
      <div className="font-bold text-slate-100 text-sm mb-4">
        Four-Pillar Risk Scores (Composite: {risk.composite_risk_score.toFixed(1)}/100)
      </div>
      <div className="space-y-3.5">
        {pillars.map((p) => (
          <div key={p.label}>
            <div className="flex justify-between text-xs text-slate-300 mb-1">
              <span>{p.label}</span>
              <span className="font-mono font-semibold">{p.score.toFixed(1)} / 100</span>
            </div>
            <div className="w-full h-6 bg-slate-800/80 rounded overflow-hidden relative">
              <div
                className="h-full transition-all duration-300 flex items-center justify-end pr-2 text-[11px] font-bold text-white"
                style={{
                  width: `${Math.max(8, p.score)}%`,
                  backgroundColor: getColor(p.score),
                }}
              >
                {p.score >= 18 ? `${p.score.toFixed(1)}` : ''}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Multi-Spectral CNN Land Cover Verification Horizontal Bar Chart
 */
export const ZoningConfidenceChart: React.FC<{
  zoning: ZoningVerificationResult;
  claimedZoning: string;
}> = ({ zoning, claimedZoning }) => {
  const entries = Object.entries(zoning.class_probabilities).sort((a, b) => b[1] - a[1]);

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
      <div className="font-bold text-slate-100 text-sm mb-3">
        Multi-Spectral CNN Land Cover Verification (13-Band Tensor)
      </div>
      <div className="space-y-2.5">
        {entries.map(([key, prob]) => {
          const pct = prob * 100;
          const isTop = key === zoning.predicted_class;
          const isClaimed = claimedZoning.toLowerCase().includes(key.split('_')[0]);
          const color = isTop ? '#10b981' : isClaimed ? '#38bdf8' : '#475569';
          const label = key
            .split('_')
            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(' ');
          return (
            <div key={key}>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>{label}</span>
                <span className="font-mono">{pct.toFixed(1)}%</span>
              </div>
              <div className="w-full h-5 bg-slate-800 rounded overflow-hidden">
                <div
                  className="h-full transition-all duration-300"
                  style={{ width: `${Math.max(3, pct)}%`, backgroundColor: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/**
 * Cross-Scenario Haircut Comparison Grouped Bar Chart
 */
export const ScenarioComparisonChart: React.FC<{
  valA: ClimateAdjustedValuation;
  valB: ClimateAdjustedValuation;
  labelA: string;
  labelB: string;
}> = ({ valA, valB, labelA, labelB }) => {
  const categories = [
    {
      name: 'Inundation Land Loss',
      a: valA.deductions.inundation_loss_inr / 1e6,
      b: valB.deductions.inundation_loss_inr / 1e6,
    },
    {
      name: 'Logistics Severance',
      a: valA.deductions.accessibility_penalty_inr / 1e6,
      b: valB.deductions.accessibility_penalty_inr / 1e6,
    },
    {
      name: 'Subsidence CapEx',
      a: valA.deductions.subsidence_capex_reserve_inr / 1e6,
      b: valB.deductions.subsidence_capex_reserve_inr / 1e6,
    },
    {
      name: 'Environmental Discount',
      a: valA.deductions.environmental_discount_inr / 1e6,
      b: valB.deductions.environmental_discount_inr / 1e6,
    },
    {
      name: 'Total Haircut',
      a: valA.deductions.total_haircut_inr / 1e6,
      b: valB.deductions.total_haircut_inr / 1e6,
    },
  ];

  const maxVal = Math.max(1, ...categories.flatMap((c) => [c.a, c.b])) * 1.15;

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4 mt-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div className="font-bold text-slate-100 text-sm">
          Cross-Scenario Haircut Comparison by Transmission Channel (INR Millions)
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-[#38bdf8] inline-block" />
            {labelA}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm bg-[#f43f5e] inline-block" />
            {labelB}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4 pt-2">
        {categories.map((cat) => (
          <div key={cat.name} className="flex flex-col items-center">
            <div className="h-40 w-full flex items-end justify-center gap-2 border-b border-slate-700 pb-1 px-2">
              <div className="flex flex-col items-center w-8">
                <span className="text-[10px] text-sky-400 font-mono mb-1">
                  ₹{cat.a.toFixed(1)}M
                </span>
                <div
                  className="w-full bg-[#38bdf8] rounded-t transition-all duration-300"
                  style={{ height: `${Math.max(4, (cat.a / maxVal) * 125)}px` }}
                />
              </div>
              <div className="flex flex-col items-center w-8">
                <span className="text-[10px] text-rose-400 font-mono mb-1">
                  ₹{cat.b.toFixed(1)}M
                </span>
                <div
                  className="w-full bg-[#f43f5e] rounded-t transition-all duration-300"
                  style={{ height: `${Math.max(4, (cat.b / maxVal) * 125)}px` }}
                />
              </div>
            </div>
            <span className="text-xs text-slate-300 text-center mt-2">{cat.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Multi-Decadal InSAR Ground Subsidence Trajectory Chart (2025-2100)
 */
export const SubsidenceTrajectoryChart: React.FC<{ subsidence: SubsidenceMetrics }> = ({
  subsidence,
}) => {
  const rateMYr = subsidence.mean_subsidence_rate_mm_year / 1000.0;
  const years = [2025, 2035, 2050, 2075, 2100];
  const central = years.map((yr) => (yr - 2025) * rateMYr);
  const upper = central.map((c) => c * 1.3);
  const lower = central.map((c) => c * 0.7);

  const maxY = Math.max(0.5, ...upper) * 1.15;
  const W = 500;
  const H = 200;
  const xPos = (i: number) => 55 + (i / (years.length - 1)) * (W - 85);
  const yPos = (val: number) => H - (val / maxY) * (H - 35) - 20;

  const polyPoints = [
    ...years.map((_, i) => `${xPos(i)},${yPos(upper[i])}`),
    ...years
      .slice()
      .reverse()
      .map((_, revIdx) => {
        const i = years.length - 1 - revIdx;
        return `${xPos(i)},${yPos(lower[i])}`;
      }),
  ].join(' ');

  const linePoints = years.map((_, i) => `${xPos(i)},${yPos(central[i])}`).join(' ');

  return (
    <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
      <div className="font-bold text-slate-100 text-sm mb-2">
        Multi-Decadal InSAR Ground Subsidence Trajectory (2025–2100)
      </div>
      <svg viewBox={`0 0 ${W} ${H + 20}`} className="w-full h-auto">
        {[0, 0.25, 0.5, 0.75, 1.0].map((f) => {
          const v = maxY * f;
          const y = yPos(v);
          return (
            <g key={f}>
              <line x1={55} y1={y} x2={W - 30} y2={y} stroke="#1e293b" strokeWidth={1} />
              <text x={48} y={y + 3} textAnchor="end" fill="#94a3b8" fontSize="9">
                {v.toFixed(2)}m
              </text>
            </g>
          );
        })}

        <polygon points={polyPoints} fill="rgba(244, 63, 94, 0.18)" />
        <polyline fill="none" stroke="#f43f5e" strokeWidth={2.5} points={linePoints} />

        {years.map((yr, i) => (
          <g key={yr}>
            <circle cx={xPos(i)} cy={yPos(central[i])} r={4} fill="#f43f5e" />
            <text
              x={xPos(i)}
              y={yPos(central[i]) - 8}
              textAnchor="middle"
              fill="#f8fafc"
              fontSize="9"
            >
              {central[i].toFixed(2)}m
            </text>
            <text x={xPos(i)} y={H + 8} textAnchor="middle" fill="#94a3b8" fontSize="10">
              {yr}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};
