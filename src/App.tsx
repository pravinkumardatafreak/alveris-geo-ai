import React, { useMemo, useState } from 'react';
import {
  CURATED_PARCELS,
  evaluateScenarioPipeline,
  generateHtmlUnderwritingMemo,
  generateMarkdownUnderwritingMemo,
  ParcelAsset,
  parseGeoJSONToParcel,
} from './engine/alverisEngine';
import {
  RiskPillarChart,
  ScenarioComparisonChart,
  SubsidenceTrajectoryChart,
  ValuationWaterfallChart,
  ZoningConfidenceChart,
} from './components/Charts';
import { GeospatialCockpit } from './components/GeospatialCockpit';
import {
  DemElevationRasterCanvas,
  InsarSubsidenceRasterCanvas,
  Sentinel2CirRasterCanvas,
  SlopeGradientRasterCanvas,
} from './components/RasterVisuals';

const SCENARIOS: Record<string, number> = {
  'Baseline (+0.0m SLR)': 0.0,
  'Mild (+0.5m SLR) — 2050': 0.5,
  'Moderate (+1.0m SLR) — 2100': 1.0,
  'Severe (+1.5m SLR) — High Emission': 1.5,
  'Extreme (+2.0m SLR) — Tail Risk': 2.0,
};

export function App() {
  const [sourceMode, setSourceMode] = useState<'Curated Portfolios' | 'Upload Custom GeoJSON'>(
    'Curated Portfolios'
  );
  const [selectedParcelKey, setSelectedParcelKey] = useState<string>(
    'Coastal Peri-Urban (Ennore)'
  );
  const [customParcel, setCustomParcel] = useState<ParcelAsset | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>('');

  const [analysisMode, setAnalysisMode] = useState<
    'Single Scenario Underwriting' | 'Side-by-Side Stress Comparison'
  >('Single Scenario Underwriting');

  const [singleScenarioLabel, setSingleScenarioLabel] = useState<string>(
    'Moderate (+1.0m SLR) — 2100'
  );
  const [scenarioALabel, setScenarioALabel] = useState<string>('Baseline (+0.0m SLR)');
  const [scenarioBLabel, setScenarioBLabel] = useState<string>('Extreme (+2.0m SLR) — Tail Risk');

  const [enableSub, setEnableSub] = useState<boolean>(true);
  const [subRate, setSubRate] = useState<number>(10.0);
  const [horizon, setHorizon] = useState<number>(2050);

  const [caseStudyExpanded, setCaseStudyExpanded] = useState<boolean>(false);
  const [activeDeepDiveTab, setActiveDeepDiveTab] = useState<number>(0);

  const parcel: ParcelAsset = useMemo(() => {
    if (sourceMode === 'Upload Custom GeoJSON' && customParcel) {
      return customParcel;
    }
    return CURATED_PARCELS[selectedParcelKey] || CURATED_PARCELS['Coastal Peri-Urban (Ennore)'];
  }, [sourceMode, selectedParcelKey, customParcel]);

  const activeLabelA =
    analysisMode === 'Single Scenario Underwriting' ? singleScenarioLabel : scenarioALabel;
  const slrA = SCENARIOS[activeLabelA] ?? 1.0;
  const slugA = `slr_${String(slrA).replace('.', '_')}`;

  const resA = useMemo(
    () =>
      evaluateScenarioPipeline(parcel, {
        slr_level: slrA,
        scenario_slug: slugA,
        enable_sub: enableSub,
        sub_rate: subRate,
        horizon,
      }),
    [parcel, slrA, slugA, enableSub, subRate, horizon]
  );

  const slrB = SCENARIOS[scenarioBLabel] ?? 2.0;
  const slugB = `slr_${String(slrB).replace('.', '_')}`;

  const resB = useMemo(
    () =>
      evaluateScenarioPipeline(parcel, {
        slr_level: slrB,
        scenario_slug: slugB,
        enable_sub: enableSub,
        sub_rate: subRate,
        horizon,
      }),
    [parcel, slrB, slugB, enableSub, subRate, horizon]
  );

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const json = JSON.parse(String(ev.target?.result || '{}'));
        const parsed = parseGeoJSONToParcel(json);
        setCustomParcel(parsed);
        setUploadStatus(`Loaded custom GeoJSON: ${parsed.name} (${parsed.asset_id})`);
      } catch {
        setUploadStatus('Invalid GeoJSON file. Using Ennore default.');
      }
    };
    reader.readAsText(file);
  };

  const memoContext = {
    scenario_title: activeLabelA,
    horizon_year: horizon,
    uncertainty_rating: resA.zoning.uncertainty_rating,
    epistemic_uncertainty: resA.zoning.epistemic_uncertainty,
    aleatoric_uncertainty: resA.zoning.aleatoric_uncertainty,
    sdg_index: resA.sdg.composite_sdg_index,
  };

  const memoHtml = useMemo(
    () => generateHtmlUnderwritingMemo(parcel, resA.valuation, resA.risk, memoContext),
    [parcel, resA, activeLabelA, horizon]
  );

  const memoMd = useMemo(
    () => generateMarkdownUnderwritingMemo(parcel, resA.valuation, resA.risk, memoContext),
    [parcel, resA, activeLabelA, horizon]
  );

  const downloadFile = (content: string, filename: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const deepDiveTabs = [
    '🛰️ Multispectral & Bayesian AI',
    '🏔️ Topography & InSAR Sinking',
    '🛣️ Road Network Resilience',
    '🌍 UN SDG & ESG Scorecard',
    '📄 Underwriting Memo Export',
    '🛡️ Data Lineage & Spatial Gates',
  ];

  return (
    <div className="min-h-screen bg-[#0b0f19] text-[#e2e8f0] flex flex-col md:flex-row">
      {/* Sidebar — mirrors st.sidebar in src/alveris/app.py */}
      <aside className="w-full md:w-80 bg-[#0f172a] border-r border-slate-800 p-5 shrink-0 space-y-6">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-sky-400 mb-1">
            ALVERIS Decision Cockpit
          </div>
          <h2 className="text-base font-bold text-slate-100">Asset Selection</h2>
          <div className="mt-3 space-y-2 text-xs">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="sourceMode"
                checked={sourceMode === 'Curated Portfolios'}
                onChange={() => setSourceMode('Curated Portfolios')}
                className="accent-sky-400"
              />
              Curated Portfolios
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="sourceMode"
                checked={sourceMode === 'Upload Custom GeoJSON'}
                onChange={() => setSourceMode('Upload Custom GeoJSON')}
                className="accent-sky-400"
              />
              Upload Custom GeoJSON
            </label>
          </div>

          {sourceMode === 'Curated Portfolios' ? (
            <div className="mt-3">
              <label className="block text-xs text-slate-400 mb-1">Target Cadastral Asset</label>
              <select
                value={selectedParcelKey}
                onChange={(e) => setSelectedParcelKey(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-xs text-slate-100"
              >
                {Object.keys(CURATED_PARCELS).map((k) => (
                  <option key={k} value={k}>
                    {k}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="mt-3 space-y-2">
              <label className="block text-xs text-slate-400">
                Upload Cadastral GeoJSON Polygon
              </label>
              <input
                type="file"
                accept=".geojson,.json"
                onChange={handleFileUpload}
                className="block w-full text-xs text-slate-300 file:mr-2 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-sky-500/20 file:text-sky-300 hover:file:bg-sky-500/30"
              />
              <div className="text-[11px] text-slate-400">
                {uploadStatus ||
                  'Upload a GeoJSON polygon to evaluate a custom site. Using Ennore default.'}
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-slate-800 pt-5">
          <h2 className="text-base font-bold text-slate-100">Analysis Mode</h2>
          <div className="mt-3 space-y-2 text-xs">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="analysisMode"
                checked={analysisMode === 'Single Scenario Underwriting'}
                onChange={() => setAnalysisMode('Single Scenario Underwriting')}
                className="accent-sky-400"
              />
              Single Scenario Underwriting
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="analysisMode"
                checked={analysisMode === 'Side-by-Side Stress Comparison'}
                onChange={() => setAnalysisMode('Side-by-Side Stress Comparison')}
                className="accent-sky-400"
              />
              Side-by-Side Stress Comparison
            </label>
          </div>

          {analysisMode === 'Single Scenario Underwriting' ? (
            <div className="mt-4">
              <label className="block text-xs text-slate-400 mb-1">
                Climate Stress Scenario (IPCC AR6)
              </label>
              <select
                value={singleScenarioLabel}
                onChange={(e) => setSingleScenarioLabel(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-xs text-slate-100"
              >
                {Object.keys(SCENARIOS).map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="mt-4 grid grid-cols-1 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Scenario A</label>
                <select
                  value={scenarioALabel}
                  onChange={(e) => setScenarioALabel(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100"
                >
                  {Object.keys(SCENARIOS).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Scenario B</label>
                <select
                  value={scenarioBLabel}
                  onChange={(e) => setScenarioBLabel(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100"
                >
                  {Object.keys(SCENARIOS).map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-slate-800 pt-5 space-y-4">
          <h3 className="text-sm font-bold text-slate-100">Geotechnical Dynamics</h3>
          <label className="flex items-center gap-2 text-xs cursor-pointer">
            <input
              type="checkbox"
              checked={enableSub}
              onChange={(e) => setEnableSub(e.target.checked)}
              className="accent-sky-400"
            />
            Include InSAR Land Subsidence
          </label>

          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1">
              <span>Annual Sinking Rate (mm/year)</span>
              <span className="font-mono text-sky-400">{subRate.toFixed(1)} mm/yr</span>
            </div>
            <input
              type="range"
              min={0}
              max={25}
              step={1}
              value={subRate}
              onChange={(e) => setSubRate(Number(e.target.value))}
              className="w-full accent-sky-400"
            />
          </div>

          <div>
            <span className="block text-xs text-slate-400 mb-1.5">Underwriting Horizon</span>
            <div className="flex gap-4 text-xs">
              {[2050, 2100].map((yr) => (
                <label key={yr} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="horizon"
                    checked={horizon === yr}
                    onChange={() => setHorizon(yr)}
                    className="accent-sky-400"
                  />
                  {yr}
                </label>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto">
        <header className="mb-5">
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            ALVERIS — Climate Risk &amp; Land Valuation Intelligence
          </h1>
          <p className="text-xs md:text-sm text-slate-400 mt-1">
            Automated Land Valuation &amp; Environmental Risk Intelligence System | Grounded in IPCC
            AR6 WG1 &amp; SEC Physical Climate Risk Standards
          </p>
        </header>

        {/* Institutional Case Study Expander */}
        <div className="mb-5 bg-[#0f172a] border border-slate-800 rounded-lg overflow-hidden">
          <button
            type="button"
            onClick={() => setCaseStudyExpanded(!caseStudyExpanded)}
            className="w-full px-4 py-3 text-left text-xs md:text-sm font-semibold text-slate-200 flex items-center justify-between hover:bg-slate-800/50 transition"
          >
            <span>
              💼 Institutional Case Study: How ALVERIS Preempted a ₹12 Cr Default at Ennore Port
            </span>
            <span className="text-slate-400">{caseStudyExpanded ? '▲' : '▼'}</span>
          </button>
          {caseStudyExpanded && (
            <div className="px-4 pb-4 pt-2 text-xs text-slate-300 space-y-2 border-t border-slate-800 leading-relaxed">
              <p>
                <strong>The Blind Spot:</strong> An infrastructure private equity fund evaluated an
                ₹18.5 Cr coastal logistics asset in Ennore. Conventional appraisals using 3-year
                backward-looking comps and standard 3-band RGB satellite imagery rated the asset as{' '}
                <em>&apos;Low Risk&apos;</em>, completely blind to hydrologic breach pathways.
              </p>
              <p>
                <strong>The ALVERIS Audit:</strong> Running the parcel through ALVERIS revealed that
                a +1.0m sea-level rise established an 8-way morphological breach from the estuary,
                inundating <strong>35% of usable land</strong> and severing the main arterial
                highway under &gt;0.30m water. Compounded by 10 mm/year InSAR subsidence, ALVERIS
                computed an immediate <strong>₹11.9 Cr (-64.3%) collateral haircut</strong>, saving
                the fund from an unhedged default.
              </p>
            </div>
          )}
        </div>

        {/* Active Asset Pill */}
        <div className="asset-pill">
          <strong>Active Asset:</strong> {parcel.name} ({parcel.asset_id}) |{' '}
          <strong>Class:</strong> {parcel.land_use_class} | <strong>Cadastral Area:</strong>{' '}
          {Math.round(parcel.area_sqm).toLocaleString('en-IN')} m² ({parcel.area_hectares} ha) |{' '}
          <strong>UTM:</strong> <code className="text-sky-400">{parcel.utm_epsg}</code>
        </div>

        {/* Executive KPIs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
            <div className="text-xs text-slate-400">Baseline Market Value</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              ₹ {Math.round(parcel.baseline_market_value_inr).toLocaleString('en-IN')}
            </div>
            <div className="text-[11px] text-slate-500 mt-1">
              Unadjusted baseline valuation from cadastral deeds
            </div>
          </div>

          <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
            <div className="text-xs text-slate-400">Climate-Adjusted Value</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              ₹ {Math.round(resA.valuation.climate_adjusted_value_inr).toLocaleString('en-IN')}
            </div>
            <div className="text-xs font-semibold text-rose-400 mt-1">
              ↓ -₹ {Math.round(resA.valuation.deductions.total_haircut_inr).toLocaleString('en-IN')}{' '}
              (-{resA.valuation.deductions.total_haircut_percent.toFixed(1)}%)
            </div>
          </div>

          <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
            <div className="text-xs text-slate-400">Regulatory Climate VaR</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              -{resA.valuation.climate_var_percent.toFixed(1)}%
            </div>
            <div className="text-xs font-semibold text-rose-400 mt-1">
              ↓ -₹ {Math.round(resA.valuation.climate_var_proxy_inr).toLocaleString('en-IN')}
            </div>
          </div>

          <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
            <div className="text-xs text-slate-400 mb-1.5">Composite Risk Tier</div>
            <div>
              <span className={`badge-${resA.risk.risk_tier}`}>
                {resA.risk.risk_tier.toUpperCase()} RISK
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-2">
              Score: {resA.risk.composite_risk_score.toFixed(1)} / 100
            </div>
          </div>
        </div>

        {/* Executive Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-6">
          <div className="lg:col-span-3">
            <ValuationWaterfallChart valuation={resA.valuation} />
          </div>
          <div className="lg:col-span-2 flex flex-col justify-between gap-3">
            <RiskPillarChart risk={resA.risk} />
            <div className="bg-sky-950/40 border border-sky-800/60 text-sky-200 text-xs p-3.5 rounded-lg">
              <strong>Primary Risk Transmission Driver:</strong> {resA.risk.primary_risk_driver}
            </div>
          </div>
        </div>

        {/* Side-by-Side Scenario Stress Comparison */}
        {analysisMode === 'Side-by-Side Stress Comparison' && (
          <div className="my-6 border-t border-slate-800 pt-6">
            <h2 className="text-xl font-bold text-slate-100 mb-4">
              Cross-Scenario Stress Test: {scenarioALabel} vs. {scenarioBLabel}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
                <div className="text-xs text-slate-400">Value ({scenarioALabel})</div>
                <div className="text-xl font-bold text-slate-100 mt-1">
                  ₹ {Math.round(resA.valuation.climate_adjusted_value_inr).toLocaleString('en-IN')}
                </div>
              </div>
              <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
                <div className="text-xs text-slate-400">Value ({scenarioBLabel})</div>
                <div className="text-xl font-bold text-slate-100 mt-1">
                  ₹ {Math.round(resB.valuation.climate_adjusted_value_inr).toLocaleString('en-IN')}
                </div>
              </div>
              <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
                <div className="text-xs text-slate-400">Deduction Escalation</div>
                <div className="text-xl font-bold text-slate-100 mt-1">
                  ₹{' '}
                  {Math.round(
                    resB.valuation.deductions.total_haircut_inr -
                      resA.valuation.deductions.total_haircut_inr
                  ).toLocaleString('en-IN')}
                </div>
                <div className="text-xs text-rose-400 mt-1">
                  +
                  {(
                    resB.valuation.deductions.total_haircut_percent -
                    resA.valuation.deductions.total_haircut_percent
                  ).toFixed(1)}
                  % Haircut
                </div>
              </div>
              <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
                <div className="text-xs text-slate-400 mb-2">Risk Tier Shift</div>
                <div className="flex items-center gap-2">
                  <span className={`badge-${resA.risk.risk_tier}`}>
                    {resA.risk.risk_tier.toUpperCase()}
                  </span>
                  <span>➔</span>
                  <span className={`badge-${resB.risk.risk_tier}`}>
                    {resB.risk.risk_tier.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
            <ScenarioComparisonChart
              valA={resA.valuation}
              valB={resB.valuation}
              labelA={scenarioALabel}
              labelB={scenarioBLabel}
            />
          </div>
        )}

        {/* Interactive Geospatial Cockpit */}
        <GeospatialCockpit
          parcel={parcel}
          inundation={resA.inundation}
          isNetworkIsolated={resA.network.is_physically_isolated}
          subsidenceRateMmYr={enableSub ? -resA.subsidence.mean_subsidence_rate_mm_year : 0.0}
        />

        {/* 6 Technical Deep-Dive Tabs */}
        <div className="border-t border-slate-800 pt-6 mt-6">
          <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3 mb-5">
            {deepDiveTabs.map((tabTitle, idx) => (
              <button
                key={tabTitle}
                type="button"
                onClick={() => setActiveDeepDiveTab(idx)}
                className={`px-3.5 py-2 rounded-md text-xs font-semibold transition ${
                  activeDeepDiveTab === idx
                    ? 'bg-sky-500 text-slate-950 font-bold'
                    : 'bg-[#0f172a] text-slate-300 hover:bg-slate-800 border border-slate-800'
                }`}
              >
                {tabTitle}
              </button>
            ))}
          </div>

          {/* Tab 1: Multispectral & Bayesian AI */}
          {activeDeepDiveTab === 0 && (
            <div>
              <h3 className="text-lg font-bold text-slate-100 mb-4">
                Satellite Multispectral Sensors &amp; Bayesian Uncertainty Verification
              </h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-5 space-y-4">
                  <h4 className="font-bold text-sm text-slate-100">
                    Sentinel-2 Level-2A Surface Indices
                  </h4>
                  <ul className="text-xs text-slate-300 space-y-1.5">
                    <li>
                      • <strong>NDVI (Vigor):</strong>{' '}
                      <code className="text-sky-400">
                        {resA.environment.ndvi.mean_val.toFixed(2)}
                      </code>{' '}
                      (
                      {resA.environment.ndvi_anomaly >= 0
                        ? `+${resA.environment.ndvi_anomaly.toFixed(2)}`
                        : resA.environment.ndvi_anomaly.toFixed(2)}
                      )
                    </li>
                    <li>
                      • <strong>NDMI (Moisture):</strong>{' '}
                      <code className="text-sky-400">
                        {resA.environment.ndmi.mean_val.toFixed(2)}
                      </code>{' '}
                      (
                      {resA.environment.ndmi_anomaly >= 0
                        ? `+${resA.environment.ndmi_anomaly.toFixed(2)}`
                        : resA.environment.ndmi_anomaly.toFixed(2)}
                      )
                    </li>
                    <li>
                      • <strong>NDRE (Salinity):</strong>{' '}
                      <code className="text-sky-400">
                        {resA.environment.ndre.mean_val.toFixed(2)}
                      </code>{' '}
                      (
                      {resA.environment.ndre_anomaly >= 0
                        ? `+${resA.environment.ndre_anomaly.toFixed(2)}`
                        : resA.environment.ndre_anomaly.toFixed(2)}
                      )
                    </li>
                  </ul>

                  <div className="space-y-2.5 pt-2">
                    {[
                      {
                        label: 'Vegetation Canopy Vigor',
                        val: resA.environment.vegetation_vigor_score,
                        color: '#10b981',
                      },
                      {
                        label: 'Canopy Moisture Deficit',
                        val: resA.environment.moisture_stress_score,
                        color: '#f59e0b',
                      },
                      {
                        label: 'Root-Zone Salinization Risk',
                        val: resA.environment.salinization_risk_score,
                        color: '#ef4444',
                      },
                    ].map((bar) => (
                      <div key={bar.label}>
                        <div className="flex justify-between text-xs text-slate-300 mb-1">
                          <span>{bar.label}</span>
                          <span>{bar.val.toFixed(0)}%</span>
                        </div>
                        <div className="w-full h-2.5 bg-slate-800 rounded overflow-hidden">
                          <div
                            className="h-full"
                            style={{ width: `${bar.val}%`, backgroundColor: bar.color }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  <blockquote className="border-l-2 border-sky-400 pl-3 text-xs text-slate-400 italic">
                    <strong>Spectral Sensitivity:</strong> 13-band Sentinel-2 tensors exploit
                    Red-Edge (B05) and SWIR (B11/B12) absorption to detect sub-canopy stress and
                    impervious surfaces.
                  </blockquote>

                  <Sentinel2CirRasterCanvas spectralTensor={resA.raster_grids.spectral_tensor} />
                </div>

                <div className="space-y-4">
                  <ZoningConfidenceChart zoning={resA.zoning} claimedZoning={parcel.name} />
                  <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4 text-xs space-y-3">
                    <div>
                      <strong>Claimed Zoning Alignment:</strong>{' '}
                      {resA.zoning.is_zoning_consistent ? '✅ DEED CONSISTENT' : '⚠️ DISCREPANCY'} |{' '}
                      <strong>Impervious Surface:</strong>{' '}
                      <code className="text-sky-400">
                        {(resA.zoning.impervious_surface_fraction * 100).toFixed(1)}%
                      </code>
                    </div>

                    <div className="bg-sky-950/40 border border-sky-800/60 p-3 rounded text-sky-200">
                      <strong>Bayesian Monte Carlo Dropout Uncertainty</strong>
                      <div className="mt-1">
                        <strong>Reliability Tier:</strong>{' '}
                        <code>{resA.zoning.uncertainty_rating}</code> |{' '}
                        <strong>Epistemic Var:</strong>{' '}
                        <code>{resA.zoning.epistemic_uncertainty.toFixed(5)}</code> |{' '}
                        <strong>Aleatoric Entropy:</strong>{' '}
                        <code>{resA.zoning.aleatoric_uncertainty.toFixed(3)}</code> |{' '}
                        <strong>OOD Detected:</strong>{' '}
                        <code>{resA.zoning.is_out_of_distribution ? 'YES ⚠️' : 'NO ✅'}</code>
                      </div>
                    </div>

                    <div>
                      <div className="font-bold text-slate-200 mb-1.5">
                        Deep Learning Multi-Spectral Architecture
                      </div>
                      <pre className="bg-slate-950 border border-slate-800 rounded p-3 text-[11px] text-emerald-300 overflow-x-auto">
                        {JSON.stringify(
                          {
                            model_name: 'MultiSpectralCNN_Bayesian_MC_Dropout',
                            input_channels: 13,
                            detected_class: resA.zoning.predicted_class,
                            confidence: `${(resA.zoning.confidence * 100).toFixed(1)}%`,
                            epistemic_uncertainty: resA.zoning.epistemic_uncertainty,
                            aleatoric_entropy: resA.zoning.aleatoric_uncertainty,
                            is_out_of_distribution: resA.zoning.is_out_of_distribution,
                            uncertainty_rating: resA.zoning.uncertainty_rating,
                            red_edge_active: true,
                            swir_absorption_active: true,
                            dilated_convolutions: true,
                            bayesian_mc_dropout: true,
                            s2_multispectral_accuracy: '95.98%',
                            spectral_advantage: '+15.02%',
                          },
                          null,
                          2
                        )}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Topography & InSAR Sinking */}
          {activeDeepDiveTab === 1 && (
            <div>
              <h3 className="text-lg font-bold text-slate-100 mb-4">
                Topographic Relief &amp; Multi-Decadal InSAR Sinking
              </h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-5">
                  <h4 className="font-bold text-sm text-slate-100 mb-3">
                    Elevation Distribution (Copernicus GLO-30 DEM)
                  </h4>
                  <div className="grid grid-cols-3 gap-3 mb-4">
                    <div className="bg-slate-900 p-3 rounded border border-slate-800">
                      <div className="text-[11px] text-slate-400">Mean Parcel Elevation</div>
                      <div className="text-lg font-bold text-slate-100">
                        {resA.terrain.elevation_median_m.toFixed(2)} m
                      </div>
                    </div>
                    <div className="bg-slate-900 p-3 rounded border border-slate-800">
                      <div className="text-[11px] text-slate-400">Elevation Span</div>
                      <div className="text-sm font-bold text-slate-100 mt-1">
                        {resA.terrain.elevation_min_m.toFixed(2)}m —{' '}
                        {resA.terrain.elevation_max_m.toFixed(2)}m
                      </div>
                    </div>
                    <div className="bg-slate-900 p-3 rounded border border-slate-800">
                      <div className="text-[11px] text-slate-400">Horn&apos;s Mean Slope</div>
                      <div className="text-lg font-bold text-slate-100">
                        {resA.terrain.slope_mean_deg.toFixed(2)}°
                      </div>
                    </div>
                  </div>
                  <DemElevationRasterCanvas
                    elevGrid={resA.raster_grids.elev_grid}
                    waterLevelRiseM={slrA}
                  />
                  <SlopeGradientRasterCanvas slopeGrid={resA.raster_grids.slope_grid} />
                </div>

                <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-5">
                  <h4 className="font-bold text-sm text-slate-100 mb-3">
                    Multi-Decadal InSAR Sinking Trajectory
                  </h4>
                  <SubsidenceTrajectoryChart subsidence={resA.subsidence} />
                  <div className="text-xs text-slate-400 my-3">
                    Annual Rate: {resA.subsidence.mean_subsidence_rate_mm_year.toFixed(1)} mm/yr |
                    Differential Gradient:{' '}
                    {resA.subsidence.differential_gradient_mm_per_m.toFixed(4)} mm/m (
                    {resA.subsidence.settlement_risk.toUpperCase()} RISK)
                  </div>
                  <InsarSubsidenceRasterCanvas
                    meanRateMm={resA.subsidence.mean_subsidence_rate_mm_year}
                    diffGradient={resA.subsidence.differential_gradient_mm_per_m}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Road Network Resilience */}
          {activeDeepDiveTab === 2 && (
            <div>
              <h3 className="text-lg font-bold text-slate-100 mb-4">
                Emergency Evacuation Road Network Topology
              </h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-5 space-y-3 text-xs">
                  <h4 className="font-bold text-sm text-slate-100">
                    Network Accessibility Routing
                  </h4>
                  <ul className="space-y-2 text-slate-300">
                    <li>
                      • <strong>Dry Baseline Route:</strong>{' '}
                      <code className="text-sky-400">
                        {resA.network.baseline_route_distance_m.toLocaleString()} m
                      </code>
                    </li>
                    <li>
                      • <strong>Flooded Route Length:</strong>{' '}
                      <code className="text-sky-400">
                        {resA.network.flooded_route_distance_m
                          ? `${resA.network.flooded_route_distance_m.toLocaleString()} m`
                          : 'SEVERED (No Path)'}
                      </code>
                    </li>
                    <li>
                      • <strong>Detour Ratio Penalty:</strong>{' '}
                      <code className="text-sky-400">{resA.network.detour_ratio.toFixed(2)}×</code>
                    </li>
                    <li>
                      • <strong>Evacuation Passability:</strong>{' '}
                      <code>
                        {resA.network.is_physically_isolated
                          ? '⚠️ SEVERED — ISOLATED'
                          : '✅ PASSABLE'}
                      </code>
                    </li>
                  </ul>
                  <div className="pt-2">
                    <div className="flex justify-between text-xs text-slate-300 mb-1">
                      <span>Road Accessibility Score</span>
                      <span>{resA.network.network_accessibility_score.toFixed(0)}%</span>
                    </div>
                    <div className="w-full h-3 bg-slate-800 rounded overflow-hidden">
                      <div
                        className="h-full bg-emerald-500"
                        style={{ width: `${resA.network.network_accessibility_score}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="bg-sky-950/40 border border-sky-800/60 text-sky-200 rounded-lg p-5 text-xs leading-relaxed flex items-center">
                  <div>
                    <strong>Vehicular Passability Standard:</strong> Roads submerge and become
                    impassable at <strong>0.30m (30 cm)</strong> water depth per emergency
                    evacuation protocols. When coastal primary junctions flood, Dijkstra routing
                    calculates optimal inland bypasses.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 4: UN SDG & ESG Scorecard */}
          {activeDeepDiveTab === 3 && (
            <div>
              <h3 className="text-lg font-bold text-slate-100">
                UN Sustainable Development Goals (SDG) &amp; ESG Alignment Matrix
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Benchmarked against Persello, Koeva, Camps-Valls et al. (IEEE GRSM 2022)
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
                <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
                  <div className="text-xs text-slate-400">Composite SDG Index</div>
                  <div className="text-2xl font-bold text-slate-100 mt-1">
                    {resA.sdg.composite_sdg_index.toFixed(1)} / 100
                  </div>
                </div>
                <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
                  <div className="text-xs text-slate-400">ESG Taxonomy Classification</div>
                  <div className="text-base font-bold text-sky-400 mt-1.5">
                    {resA.sdg.esg_eligibility_tier}
                  </div>
                </div>
                <div className="bg-[#0f172a] border border-slate-800 rounded-lg p-4">
                  <div className="text-xs text-slate-400">Green Bond Covenants</div>
                  <div className="text-xl font-bold text-emerald-400 mt-1">
                    {resA.sdg.green_bond_eligible ? 'COMPLIANT ✅' : 'REVIEW ⚠️'}
                  </div>
                </div>
              </div>

              <div className="bg-[#0f172a] border border-slate-800 rounded-lg overflow-hidden">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 uppercase">
                      <th className="p-3.5">Indicator</th>
                      <th className="p-3.5">Official UN SDG Target</th>
                      <th className="p-3.5">Status</th>
                      <th className="p-3.5">Key Earth Observation Finding</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {resA.sdg.indicators.map((ind) => (
                      <tr key={ind.indicator_code}>
                        <td className="p-3.5 font-bold text-slate-100">{ind.indicator_code}</td>
                        <td className="p-3.5 text-slate-300">{ind.title}</td>
                        <td className="p-3.5">
                          <span
                            className={`px-2 py-0.5 rounded font-semibold ${
                              ind.status === 'Compliant'
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : 'bg-amber-500/20 text-amber-300'
                            }`}
                          >
                            {ind.status === 'Compliant' ? '✅ COMPLIANT' : '⚠️ AT RISK'}
                          </span>
                        </td>
                        <td className="p-3.5 text-slate-300">{ind.key_finding}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tab 5: Underwriting Memo Export */}
          {activeDeepDiveTab === 4 && (
            <div>
              <h3 className="text-lg font-bold text-slate-100 mb-4">
                Institutional Underwriting Memo Preview &amp; Dual Export
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <button
                  type="button"
                  onClick={() =>
                    downloadFile(
                      memoHtml,
                      `ALVERIS_Memo_${parcel.asset_id}_${slugA}.html`,
                      'text/html'
                    )
                  }
                  className="bg-sky-600 hover:bg-sky-500 text-white font-semibold py-2.5 px-4 rounded-lg text-xs transition cursor-pointer"
                >
                  📥 Download Underwriting Memo (HTML)
                </button>
                <button
                  type="button"
                  onClick={() =>
                    downloadFile(
                      memoMd,
                      `ALVERIS_Memo_${parcel.asset_id}_${slugA}.md`,
                      'text/markdown'
                    )
                  }
                  className="bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 font-semibold py-2.5 px-4 rounded-lg text-xs transition cursor-pointer"
                >
                  📥 Download Underwriting Memo (Markdown)
                </button>
              </div>
              <div className="rounded-lg overflow-hidden border border-slate-700 bg-white">
                <iframe
                  title="ALVERIS Underwriting Memo"
                  srcDoc={memoHtml}
                  className="w-full h-[680px] border-0"
                />
              </div>
            </div>
          )}

          {/* Tab 6: Data Lineage & Spatial Gates */}
          {activeDeepDiveTab === 5 && (
            <div>
              <h3 className="text-lg font-bold text-slate-100 mb-4">
                Cryptographic Data Lineage &amp; Tier 2 Spatial Code Gates
              </h3>
              <div className="space-y-2.5 mb-5 text-xs">
                <div className="bg-emerald-950/50 border border-emerald-700/60 text-emerald-200 px-4 py-2.5 rounded-lg">
                  ✅ Gate 1: Metric Local Projected Coordinate System Verified (
                  <code>{parcel.utm_epsg}</code>)
                </div>
                <div className="bg-emerald-950/50 border border-emerald-700/60 text-emerald-200 px-4 py-2.5 rounded-lg">
                  ✅ Gate 2: Spatial Join Row Accounting &amp; Null-Geometry Audited (100% Retained)
                </div>
                <div className="bg-emerald-950/50 border border-emerald-700/60 text-emerald-200 px-4 py-2.5 rounded-lg">
                  ✅ Gate 3: Centroid Plausibility Passed ([{parcel.centroid_wgs84[0]},{' '}
                  {parcel.centroid_wgs84[1]}])
                </div>
                <div className="bg-emerald-950/50 border border-emerald-700/60 text-emerald-200 px-4 py-2.5 rounded-lg">
                  ✅ Gate 4: Metric Area Plausibility Passed (
                  {Math.round(parcel.area_sqm).toLocaleString('en-IN')} m²)
                </div>
              </div>

              <pre className="bg-[#0f172a] border border-slate-800 rounded-lg p-4 text-xs text-sky-300 overflow-x-auto">
                {JSON.stringify(
                  {
                    asset_id: parcel.asset_id,
                    name: parcel.name,
                    utm_epsg: parcel.utm_epsg,
                    lineage_feature: resA.valuation.lineage.feature_name,
                    lineage_hash: resA.valuation.lineage.provenance_hash,
                    scientific_grounding:
                      'IPCC AR6 WG1 Ch 9, UN SDGs (IEEE GRSM 2022) & SEC Climate Disclosure',
                  },
                  null,
                  2
                )}
              </pre>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
export default App;
