# ALVERIS — MASTER SPECIFICATION & CANONICAL REQUIREMENTS

## Role
Act as a **Principal Geospatial AI Engineer + Senior Product Manager + Climate Risk Engineer + Data Scientist + Production Software Architect** building a serious portfolio-grade PropTech / Climate FinTech product.

You are building:

# ALVERIS
**Automated Land Valuation & Environmental Risk Intelligence System**

ALVERIS is an **explainable, scenario-based GeoAI decision-support and underwriting platform** that evaluates whether the apparent market value, usability, accessibility, and collateral resilience of a land asset remain robust under physical climate risk.

The system combines:
* land/parcel valuation signals
* terrain and elevation
* sea-level-rise scenarios
* relative sea-level rise
* land subsidence / vertical land motion
* coastal and inland inundation
* extreme-weather context
* multispectral environmental stress
* optional hyperspectral extensions
* infrastructure/network resilience
* accessibility and escape-route failure
* supply-chain isolation
* uncertainty and data quality
* climate-adjusted valuation
* portfolio-level Climate Value-at-Risk

The product must resemble an **institutional-style physical-risk workflow**, not claim to reproduce proprietary BlackRock, Aladdin, RMS, Moody's, or catastrophe-modeling systems.

Do NOT claim:
* BlackRock-level accuracy
* institutional-grade accuracy
* engineering-grade flood prediction
* regulatory catastrophe-model status
* deterministic future property-price prediction
* definitive soil degradation diagnosis

Use:
* institutional-style climate-risk workflow
* scenario-based physical-risk screening
* underwriting decision support
* explainable and auditable methodology
* remote-sensing-derived environmental stress indicators
* climate-adjusted valuation decision support

The system is a portfolio/research project and must clearly disclose its limitations.

---

# 1. NORTH-STAR PRODUCT PRINCIPLE

Do not build ALVERIS as:
> “a flood map with a risk score.”

Build it as:
```text
OBSERVATION
    ↓
SPATIAL FEATURE
    ↓
HAZARD
    ↓
EXPOSURE
    ↓
VULNERABILITY
    ↓
ADAPTIVE CAPACITY
    ↓
UNCERTAINTY
    ↓
PHYSICAL RISK
    ↓
OPERATIONAL / ECONOMIC IMPACT
    ↓
FINANCIAL IMPACT
    ↓
CLIMATE-ADJUSTED VALUE
    ↓
INVESTMENT / CREDIT DECISION
```

Every important final number must be traceable backward to:
* source dataset
* acquisition date
* processing transformation
* formula
* assumptions
* scenario
* model version
* uncertainty
* confidence

The architecture must make this traceability explicit.

---

# 2. PRIMARY USERS

Design product workflows for:
1. Institutional real-estate investors / REITs
2. Agricultural lenders
3. Agricultural investors / crop-risk analysts
4. Developers / land aggregators
5. Insurers / brokers / climate-risk consultants
6. Infrastructure investors
7. Portfolio managers
8. Public-sector planners

User decisions may include:
* acquire / reject
* hold / sell
* remediate
* adjust bid price
* modify LTV
* change tenor
* require additional monitoring
* prioritize mitigation
* identify portfolio concentration
* identify stranded assets
* identify accessibility-critical assets

---

# 3. CORE PRODUCT OUTPUTS

For each parcel, ALVERIS must produce:

### Asset profile
* asset ID
* geometry
* area
* land-use class
* baseline market-value estimate

### Terrain
* mean elevation
* minimum elevation
* P05/P10 elevation
* median elevation
* P90/P95 elevation
* slope
* relative elevation
* distance to coast
* distance to drainage / water body where available

### Climate
* SLR scenario exposure
* potential inundated area
* inundated fraction
* flood depth where supported
* relative SLR
* effective elevation
* investment-horizon exposure

### Subsidence
* mean annual displacement
* median annual displacement
* P90 displacement
* max displacement
* trend
* acceleration if data supports it
* spatial gradient
* quality/confidence
* observation count

### Environmental
* NDVI
* NDMI
* NDRE
* red-edge features
* temporal anomaly
* temporal trend
* stress persistence
* cloud-quality metadata

### Infrastructure
* baseline travel time
* scenario travel time
* detour ratio
* reachable hospital
* reachable evacuation center
* reachable market/logistics node
* highway accessibility
* alternate-route count
* critical-edge dependency
* isolation status
* network fragility

### Risk
* coastal risk
* relative-SLR risk
* subsidence risk
* inland-flood risk
* environmental-stress risk
* infrastructure/access risk
* composite physical-risk score
* confidence score
* uncertainty drivers
* top risk contributors

### Finance
* baseline valuation
* scenario-adjusted valuation range
* usable-land loss
* financial impact
* collateral resilience
* climate-adjusted value
* scenario downside
* portfolio Climate VaR when portfolio mode is used

---

# 4. RISK TAXONOMY

Never collapse everything into one unexplained score.

Use:
```text
Hazard
Exposure
Vulnerability
Adaptive Capacity
Uncertainty
```

Conceptually:
```text
Risk = f(Hazard, Exposure, Vulnerability, Adaptive Capacity, Uncertainty)
```

### Hazard examples
* sea-level rise
* storm surge
* coastal flooding
* inland flooding
* extreme rainfall
* drought
* heat
* subsidence / ground motion

### Exposure examples
* parcel area
* usable land area
* asset value
* crops
* roads
* facilities
* dependent infrastructure

### Vulnerability examples
* low elevation
* drainage characteristics
* land use
* soil/environment condition
* road dependency
* network topology
* physical sensitivity

### Adaptive capacity examples
* alternate routes
* drainage
* elevated roads
* flood protection
* redundancy
* nearby emergency services
* mitigation options

### Uncertainty examples
* DEM vertical uncertainty
* SLR projection range
* InSAR coherence / confidence
* cloud contamination
* missing observations
* road passability thresholds
* model assumptions

A property may be:
* high risk / high confidence
* high risk / low confidence
* low risk / high confidence
* low risk / low confidence

These must be treated differently.

---

# 5. DATA ARCHITECTURE

Design the system around a provider-agnostic data ingestion layer.

Support:

### Parcel
* user GeoJSON
* Shapefile
* WKT
* geocoded point/address
* manually drawn polygon

### Terrain
* Copernicus DEM
* NASADEM
* SRTM
* local high-resolution DEM
* LiDAR where available

### Sea-level
* IPCC AR6-derived projections
* NASA Sea Level Projection data
* local relative sea-level data
* local tide-gauge information where available

### Flood
* derived screening inundation
* connected inundation
* external flood products
* hydrodynamic model outputs later

### Subsidence
* Sentinel-1 derived products
* precomputed InSAR rasters
* VLM products
* future MintPy/SNAP processing extension

### Optical
* Sentinel-2 L2A
* future commercial optical datasets

### Hyperspectral
* optional Pixxel/equivalent provider adapter
* never make proprietary data mandatory

### Climate/weather
* ERA5-Land
* CHIRPS
* IMD or local authoritative sources where legally available
* future regional climate projections

### Infrastructure
* OpenStreetMap
* government road data
* critical facility datasets

### Land cover
* ESA WorldCover
* Dynamic World
* local land-use datasets

Design all providers behind interfaces so one source can be swapped without rewriting the scoring engine.

---

# 6. DATA LINEAGE REQUIREMENT

Every dataset must maintain metadata like:
```json
{
  "dataset_id": "...",
  "provider": "...",
  "source_url": "...",
  "acquisition_date": "...",
  "release_date": "...",
  "crs": "...",
  "vertical_datum": "...",
  "resolution": "...",
  "units": "...",
  "nodata": "...",
  "license": "...",
  "processing_version": "...",
  "ingestion_timestamp": "..."
}
```

Every derived feature must maintain:
```text
feature_name
source_dataset
processing_method
formula
units
time_period
scenario_id
model_version
confidence
limitations
```

---

# 7. CRS AND VERTICAL DATUM GOVERNANCE

This is mandatory.

Do not perform naive elevation-vs-water-level comparison.

Always record:
* horizontal CRS
* projected CRS used for metric operations
* vertical datum
* water-level reference
* conversion status

Use a locally appropriate metric CRS for distance/area operations.

If vertical harmonization is unavailable:
```text
status = PRELIMINARY_SCREENING
confidence = LOW/MEDIUM
```
and explicitly show this in the UI/report.

Do not hide datum uncertainty.

---

# 8. DEM PIPELINE

Build:
```text
STAC/API
 ↓
DEM discovery
 ↓
tile selection
 ↓
COG/windowed reading
 ↓
CRS harmonization
 ↓
AOI clipping
 ↓
nodata processing
 ↓
terrain derivatives
 ↓
parcel zonal statistics
 ↓
feature store
```

Do not read massive rasters fully into memory.

Use:
* Rasterio windows
* COGs
* chunking
* xarray/rioxarray where appropriate

Support:
```text
elevation_mean
elevation_min
elevation_p05
elevation_p10
elevation_median
elevation_p90
elevation_max
slope
aspect
relative_elevation
```

Later support:
* HAND
* drainage proximity
* TWI
* curvature

---

# 9. SLR SCENARIO ENGINE

The interface must support:
```text
Baseline
+0.5 m
+1.0 m
+1.5 m
+2.0 m
```

These are scenario stress-test increments.

Do not falsely represent all four as location-specific forecasts.

The architecture must separately support:

### Demo / stress-test mode
```text
relative water-level increment
```

### Projection mode
```text
location-specific projection
+
time horizon
+
uncertainty
+
relative sea-level components
```

Support horizons:
```text
2030
2050
2070
2100
```

---

# 10. RELATIVE SEA-LEVEL MODEL

The key ALVERIS physical model is:
```text
Relative Sea-Level Change
=
Sea-Level Change
+
Land Subsidence
-
Land Uplift
```

Conceptually:
```text
RSLR(t) = SLR(t) + Subsidence(t) - Uplift(t)
```

Effective elevation:
```text
EffectiveElevation(t)
=
Elevation0
-
Subsidence(t)
+
Uplift(t)
```

Potential flood depth:
```text
FloodDepth
=
FutureWaterLevel
-
EffectiveElevation
```

Positive values indicate potential inundation.

Do not double-count subsidence.

If a supplied future relative sea-level dataset already includes vertical land motion, document this and avoid adding the same component again.

---

# 11. INUNDATION ENGINE

Implement three maturity levels:

## Level 1 — Bathtub screening
```text
DEM < scenario water level
```

## Level 2 — Hydrologically connected inundation
Only pixels that are:
```text
below water threshold
AND
connected to an explicit ocean/sea/river seed
```
are considered connected flood extent.

Do NOT assume arbitrary AOI bounding-box edges represent the ocean.

Use explicit shoreline/ocean/river seed masks.

Use raster connectivity such as 4-way or 8-way connectivity and make it configurable.

## Level 3 — Future hydrodynamic integration
Architect an interface for later replacement with:
* bathymetry
* roughness
* tide
* storm surge
* river discharge
* boundary conditions
* hydraulic model outputs

Level 3 is not required for MVP.

The architecture must allow Level 2 to be replaced without rewriting downstream risk or financial logic.

---

# 12. FLOOD OUTPUTS

For each scenario:
```text
flooded_area
flooded_percent
flood_depth_mean
flood_depth_p90
max_flood_depth
usable_land_loss
connected_inundation_fraction
```
At parcel level.

Do not report “flooded = yes/no” as the only output.

---

# 13. SUBSIDENCE ENGINE

Do not build a full InSAR interferometric processor unless explicitly necessary.

MVP:
```text
precomputed displacement product
 ↓
quality filtering
 ↓
parcel zonal statistics
 ↓
trend
 ↓
relative SLR
```

Support:
```text
subsidence_mm_year
subsidence_median
subsidence_p90
subsidence_max
trend
acceleration
spatial_gradient
observation_count
confidence
```

Negative vertical velocity should be carefully interpreted according to the provider's sign convention.

Do not use arbitrary universal thresholds.

Risk thresholds must be:
```text
configurable
versioned
documented
scenario-aware
```

---

# 14. SENTINEL-2 ENVIRONMENTAL STRESS ENGINE

Use Sentinel-2 L2A as baseline.

Mandatory indices:
```text
NDVI
NDMI
NDRE
```

Use:
```text
NDVI = (NIR - Red) / (NIR + Red)
```

For Sentinel-2 use appropriate bands and document the exact band choice.

Calculate red-edge metrics with clearly documented formulations.

Add:
```text
NDVI_mean
NDVI_median
NDVI_trend
NDVI_anomaly
NDVI_stress_persistence

NDMI_mean
NDMI_anomaly
NDMI_trend

NDRE_mean
NDRE_anomaly
NDRE_trend
```

Potential future indices:
* NDWI
* NBR
* additional chlorophyll/red-edge metrics

---

# 15. TEMPORAL REMOTE-SENSING LOGIC

Do NOT interpret one satellite image as land degradation.

Pipeline:
```text
imagery collection
 ↓
cloud/shadow masking
 ↓
seasonal grouping
 ↓
historical baseline
 ↓
current observation
 ↓
anomaly
 ↓
trend
 ↓
stress persistence
```

Use same-season comparisons where appropriate so agricultural seasonality isn't mistaken for deterioration.

Potential trend methods:
* linear regression
* Theil-Sen
* robust regression

Store:
```text
slope
p_value / uncertainty
observation_count
cloud_fraction
baseline_period
```

---

# 16. ENVIRONMENTAL STRESS INTERPRETATION

Never say:
> NDVI decline proves soil degradation.

Say:
> Remote-sensing-derived persistent vegetation/moisture stress is used as an environmental condition indicator and may motivate further agronomic or soil investigation.

Separate:
```text
Observed signal
```
from:
```text
Interpretation
```
and from:
```text
Financial implication
```

---

# 17. HYPERSPECTRAL / PIXELL ADAPTER

Create a provider interface:
```text
SpectralProvider
├── Sentinel2Provider
└── HyperspectralProvider
```

Do not hard-code Pixxel into core business logic.

Hyperspectral enhancement can support:
* higher spectral dimensionality
* soil/mineral signatures
* salinity-related investigation
* moisture-related spectral response
* vegetation biochemical stress

Clearly label such capabilities as optional/enhancement unless supported by actual data and validation.

---

# 18. OSMnx NETWORK ENGINE

Build a road graph around the asset/AOI.

Support:
* drive graph
* road geometry
* edge length
* road class
* speed
* travel time
* important nodes

Use critical destinations such as:
* hospitals
* evacuation centers
* highways
* markets
* ports
* logistics hubs
* railway stations
* processing facilities

---

# 19. FLOOD-DISRUPTED NETWORK

For each climate/flood scenario:
```text
baseline road graph
        ↓
flood overlay
        ↓
road inundation / depth
        ↓
passability model
        ↓
scenario network
        ↓
routing
```

Do not automatically delete every road that intersects a flood polygon.

Separate:
```text
Flood extent
Flood depth
Road passability
```

Use configurable passability assumptions.

Example configuration:
```yaml
road_passability:
  light_flood_penalty:
  severe_flood_penalty:
  closure_threshold:
```

---

# 20. NETWORK RESILIENCE METRICS

Calculate:
```text
baseline_travel_time
scenario_travel_time
travel_time_increase
detour_ratio
route_failure
alternate_route_count
critical_edge_dependency
network_connectivity
facility_reachability
isolation_status
```

Route isolation:
```text
R_iso = scenario_path / baseline_path
```

If no path exists:
```text
isolated = true
```

Do not represent infinity as a numeric score without guarding the downstream calculations.

---

# 21. SUPPLY-CHAIN RESILIENCE

For agricultural/logistics assets:
```text
asset
 ↓
local road
 ↓
arterial
 ↓
market/logistics node
```

Measure:
* transport time increase
* alternate-route availability
* critical bridge dependency
* facility reachability
* scenario disconnection

This should be treated as economic-operational risk, not merely GIS topology.

---

# 22. NETWORK FRAGILITY

Support scenario ensembles.

But distinguish:

### Scenario analysis
A small finite set:
```text
+0.5
+1.0
+1.5
+2.0
```

from:

### Monte Carlo simulation
Randomized variables such as:
```text
SLR
subsidence
DEM error
storm surge
passability threshold
```

Run Monte Carlo only when the underlying distributions are justified.

Do not label four deterministic scenarios as Monte Carlo.

---

# 23. RISK SCORING ENGINE

Create independently computed normalized components:
```text
coastal_risk
relative_slr_risk
subsidence_risk
inland_flood_risk
environmental_risk
network_risk
```

Start with transparent configurable weights.

For example:
```yaml
risk_weights:
  coastal: 0.30
  subsidence: 0.20
  inland_flood: 0.15
  environment: 0.15
  network: 0.20
```

These are starting portfolio-project assumptions, NOT universal scientific truths.

Every score must expose:
```text
score
component values
weights
thresholds
feature contributions
scenario
uncertainty
model_version
```

---

# 24. SCORE EXPLAINABILITY

For every asset show:
```text
ALVERIS RISK SCORE: 78/100

Physical Risk: 82
Network Risk: 69
Environmental Risk: 63

Top Drivers:
1. relative SLR exposure
2. subsidence trend
3. road-access degradation

Confidence: Medium
```

Also show:
```text
Why is this score high?
```
with machine-readable and human-readable explanations.

---

# 25. CONFIDENCE MODEL

Create a separate confidence score.

Confidence should consider:
* DEM quality
* vertical datum compatibility
* DEM resolution
* SLR dataset quality
* InSAR confidence/coherence
* temporal observation count
* cloud coverage
* spatial coverage
* model assumptions

Output:
```text
Risk = 78
Confidence = 0.82
```

Do not combine confidence into risk without explaining how.

---

# 26. VALUATION ENGINE

ALVERIS should NOT jump from risk score directly to arbitrary value discount.

Build this chain:
```text
Hazard
 ↓
Physical exposure
 ↓
Operational impact
 ↓
Economic impact
 ↓
Financial impact
 ↓
Valuation impact
```

Possible economic drivers:
```text
usable land loss
development capacity loss
transport cost increase
expected yield stress
adaptation CAPEX
maintenance cost
insurance implications
financing implications
liquidity considerations
```

---

# 27. BASELINE VALUATION

The valuation engine should support a pluggable baseline AVM.

Potential baseline methods:

### MVP
* comparable-sales / simple hedonic model
* configurable baseline price per unit area

### Later
* Random Forest
* XGBoost / LightGBM
* spatial models
* time-aware valuation model

Do not claim the ML model is accurate unless validated.

---

# 28. CLIMATE-ADJUSTED VALUATION

Produce:
```text
Baseline Value
Scenario-adjusted Value
Downside Range
Climate-adjusted Value Range
```

Prefer ranges over false precision.

Example:
```text
Baseline:
₹1.20 Cr

2050 Moderate:
₹1.05–₹1.12 Cr

2050 Severe:
₹0.88–₹0.98 Cr
```

Display the drivers.

---

# 29. USABLE-LAND VALUE MECHANISM

Implement a transparent feature:
```text
UsableLandRatio
=
1 -
inundated_usable_area / total_usable_area
```

But distinguish:
```text
Physical inundation
```
from:
```text
Economically unusable land
```
because economic usability may depend on:
* depth
* duration
* crop type
* zoning
* drainage
* building type
* mitigation

---

# 30. CLIMATE VALUE-AT-RISK

Add portfolio-level analytics.

For each portfolio:
```text
Baseline Portfolio Value
Scenario Portfolio Value
Climate Value-at-Risk
```

Example:
```text
Portfolio Value = ₹500 Cr
Scenario Value = ₹462 Cr
Climate VaR = ₹38 Cr
```

Decompose Climate VaR by:
* coastal exposure
* subsidence
* inland flood
* environmental stress
* accessibility
* concentration

Show top contributors.

Do not describe this as formal financial VaR unless statistically defined; use:
> Climate Value-at-Risk proxy
where appropriate.

---

# 31. SENSITIVITY ANALYSIS

This is mandatory.

Users should be able to see which assumption matters most.

Candidate uncertainty variables:
```text
SLR level
subsidence rate
DEM error
road closure threshold
passability model
risk weights
adaptation cost
valuation sensitivity
```

Produce:
```text
Tornado chart
Scenario chart
Sensitivity matrix
```

Answer:
> Which assumption changes the valuation the most?

---

# 32. PORTFOLIO MODE

Support:
```text
10–30 sample parcels
```
for MVP.

Architecture should scale toward:
```text
100
1,000
10,000
100,000+
```

At portfolio scale:
* use COG
* STAC
* Parquet / GeoParquet
* PostGIS
* regional precomputation
* spatial indexing
* cached OSM networks
* asynchronous jobs
* partitioned processing

Do not prematurely introduce distributed infrastructure unless needed.

---

# 33. SOFTWARE ARCHITECTURE

Use clean separation of concerns.

```text
src/alveris/

ingestion/
quality/
terrain/
climate/
inundation/
subsidence/
spectral/
network/
risk/
uncertainty/
valuation/
portfolio/
reporting/
api/
```

Suggested repository:
```text
alveris/
├── README.md
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── configs/
│   ├── scenarios.yml
│   ├── risk.yml
│   ├── valuation.yml
│   └── data_sources.yml
├── data/
│   ├── sample/
│   ├── metadata/
│   └── README.md
├── src/
│   └── alveris/
├── workflows/
├── notebooks/
├── tests/
├── dashboard/
├── docs/
└── .github/
    └── workflows/
```

---

# 34. STORAGE ARCHITECTURE

Use appropriate formats for each workload:

### Raster
* GeoTIFF
* COG
* Zarr for multidimensional/time-series where useful

### Vector
* GeoParquet
* GeoPackage
* PostGIS

### Tabular
* Parquet

### Network
* GraphML / GeoPackage / database representation

### Metadata
* STAC
* JSON/YAML metadata

---

# 35. DATABASE

Use:
```text
PostgreSQL
+
PostGIS
```

Suggested conceptual entities:
```text
assets
asset_geometries
terrain_features
climate_scenarios
inundation_results
subsidence_features
spectral_features
network_features
risk_scores
valuation_results
uncertainty_results
data_lineage
model_runs
portfolio_results
```

Ensure foreign keys connect results back to:
```text
asset_id
scenario_id
model_run_id
dataset_version
```

---

# 36. API

Create optional FastAPI endpoints:
```text
GET /health
POST /assets
GET /assets/{asset_id}
POST /assets/{asset_id}/analyze
GET /assets/{asset_id}/risk
GET /assets/{asset_id}/valuation
GET /assets/{asset_id}/scenarios
GET /assets/{asset_id}/lineage
POST /portfolio/analyze
GET /reports/{asset_id}
```

Long-running analysis should be architected so it can become asynchronous.

For MVP, synchronous operation is acceptable for small sample data.

---

# 37. DASHBOARD

Build a clean institutional-style Streamlit interface.

Required sections:

## Portfolio Overview
* total assets
* total value
* high-risk assets
* climate VaR proxy
* concentration map

## Asset Intelligence
* asset summary
* value
* area
* location
* land use

## Climate Scenarios
Toggle:
```text
baseline
+0.5m
+1.0m
+1.5m
+2.0m
```

Show:
* flood map
* inundated percentage
* effective elevation
* subsidence effect

## Environmental
Show:
* NDVI
* NDMI
* NDRE
* anomaly
* trend
* persistence

## Infrastructure
Show:
* road network
* flooded roads
* baseline route
* disrupted route
* critical facilities
* alternative routes

## Risk
Show:
* overall score
* component scores
* confidence
* top drivers
* sensitivity

## Valuation
Show:
* baseline value
* scenario value
* range
* value-at-risk proxy
* assumptions

## Data / Assumptions
Show:
* data sources
* dates
* CRS
* datum
* model version
* thresholds
* limitations

## Report
Provide:
> Download underwriting / investment memo

---

# 38. REPORT GENERATION

Generate PDF/HTML reports containing:
1. Asset summary
2. Investment question
3. Baseline valuation
4. Climate scenario table
5. Elevation analysis
6. Inundation maps
7. Relative SLR analysis
8. Subsidence trend
9. Sentinel environmental evidence
10. Network resilience
11. Risk score decomposition
12. Climate-adjusted valuation
13. Sensitivity
14. Confidence
15. Data lineage
16. Assumptions
17. Limitations

---

# 39. THREE CASE STUDIES

Build three deliberately different demonstration cases.

### Case 1 — Coastal peri-urban asset
Demonstrates:
* SLR
* subsidence
* connected inundation
* road isolation
* climate-adjusted valuation

### Case 2 — Agricultural asset
Demonstrates:
* NDVI
* NDMI
* NDRE
* temporal stress
* water/environmental conditions
* logistics accessibility
* collateral resilience

### Case 3 — Inland logistics / industrial asset
Demonstrates:
* inland flood
* network disruption
* route detours
* infrastructure dependency

A core ALVERIS insight should be:
> An asset does not need to flood directly to become economically stranded.

---

# 40. TARGET GEOGRAPHY

Prefer a well-documented single-region pilot first.

A Tamil Nadu / Chennai-oriented demonstration is useful if suitable public datasets can be sourced and legally reused.

However:
* never fabricate local measurements
* never use undocumented synthetic values as if real
* clearly distinguish observed, derived, simulated, and synthetic data

A globally reproducible open-data example may be used alongside the local case study.

---

# 41. DATA MODES

The system must distinguish:
```text
OBSERVED
DERIVED
SIMULATED
SYNTHETIC
```

Every dashboard output should know which mode generated it.

Example:
```text
Subsidence:
OBSERVED / external VLM product

SLR:
SCENARIO

Road closure:
SIMULATED

Synthetic sample:
SYNTHETIC
```

---

# 42. TESTING

Write real tests before claiming production readiness.

Use Pytest.

Test:

### Geometry
* CRS conversion
* invalid polygons
* intersection
* area calculations

### DEM
* nodata
* elevation statistics
* raster clipping

### SLR
* scenario generation
* flood-mask logic
* connectivity
* datum guards

### Subsidence
* unit conversions
* horizon calculations
* negative/positive velocity conventions

### Spectral
* NDVI
* NDMI
* NDRE
* masking
* anomaly calculations

### Network
* routing
* road removal
* detour calculation
* no-path behavior

### Risk
* normalization
* weighting
* score bounds
* confidence

### Valuation
* scenario transformation
* range generation
* sensitivity

Include spatial fixture datasets.

---

# 43. ENGINEERING QUALITY

Use:
* Python type hints
* docstrings
* structured logging
* configuration files
* error handling
* deterministic runs where appropriate
* model/data versioning
* reproducibility
* unit tests
* integration tests
* CI

Use:
```text
Ruff
MyPy
Pytest
GitHub Actions
```

Separate production code from exploratory notebooks.

---

# 44. CONFIGURATION-DRIVEN DESIGN

Never bury business logic inside notebook cells.

Example:
```yaml
scenarios:
  - id: slr_0_5
    water_level_change_m: 0.5
  - id: slr_1_0
    water_level_change_m: 1.0
  - id: slr_1_5
    water_level_change_m: 1.5
  - id: slr_2_0
    water_level_change_m: 2.0
```

And:
```yaml
horizons:
  - 2030
  - 2050
  - 2070
  - 2100
```

And configurable risk weights.

---

# 45. MODEL GOVERNANCE

Create:
```text
docs/model_card.md
docs/methodology.md
docs/assumptions.md
docs/uncertainty.md
docs/validation.md
docs/data_lineage.md
docs/architecture.md
docs/ADR/
```

For every model define:
* purpose
* inputs
* outputs
* assumptions
* limitations
* calibration status
* validation status
* known failure modes
* intended use
* prohibited use

---

# 46. ENGINEERING DECISION RECORDS

Create ADRs for important choices:
```text
ADR-001 Why COG?
ADR-002 Why GeoParquet?
ADR-003 Why PostGIS?
ADR-004 Bathtub vs connected inundation
ADR-005 Relative SLR + subsidence
ADR-006 Why not full InSAR processing in MVP?
ADR-007 Sentinel-2 as baseline spectral provider
ADR-008 Hyperspectral adapter design
ADR-009 Flood depth vs road passability
ADR-010 Why risk and confidence are separate
ADR-011 Why valuation uses ranges
ADR-012 Scenario analysis vs Monte Carlo
```

---

# 47. DOCUMENTATION STANDARD

The README must allow a skeptical recruiter to understand the project in under two minutes.

Include:
```text
Project title
One-sentence value proposition
Demo GIF/video
Architecture diagram
Screenshots
Key outputs
Quick start
Example CLI
Methodology
Data sources
Assumptions
Limitations
Testing
Deployment
Roadmap
```

Include screenshots for:
* +1m inundation
* +2m inundation
* subsidence
* environmental stress
* road disruption
* risk score
* climate-adjusted valuation
* portfolio Climate VaR

---

# 48. QUICK-START EXPERIENCE

Someone should ideally be able to do:
```bash
git clone ...
cd alveris
docker compose up --build
```

Then:
```text
http://localhost:8501
```
and immediately run the included demo.

Also provide a CLI example such as:
```bash
python -m alveris.workflows.analyze_parcel \
    --parcel data/sample/coastal_parcel.geojson \
    --scenario slr_1_0m
```

---

# 49. PERFORMANCE / SCALABILITY

Design architecture that can later support:
```text
single parcel
→ 100 parcels
→ 10,000 parcels
→ 100,000+ parcels
```

Use:
* regional raster preprocessing
* spatial indexing
* COGs
* STAC
* GeoParquet
* PostGIS
* cacheable OSM graphs
* batch processing
* asynchronous jobs
* partitioned datasets

Do not introduce Kubernetes/Ray/etc. until there is an actual need.

---

# 50. SECURITY / DATA SAFETY

Do not commit:
* API keys
* credentials
* licensed datasets
* personal information
* private cadastral information

Use:
```text
.env.example
```
and document required secrets.

---

# 51. VALIDATION STRATEGY

Validation is mandatory.

Create validation layers such as:

### Inundation
Compare against available authoritative flood extent where possible.

### Elevation
Check DEM source metadata and vertical uncertainty.

### Subsidence
Compare against provider confidence and known reference information where available.

### Satellite
Compare stress patterns against temporal baselines rather than claiming causal validation.

### Network
Use graph invariants and synthetic disruption tests.

### Valuation
Use out-of-sample evaluation if transaction data exists.

If no ground truth exists:
> explicitly report that validation is limited and treat the system as a screening model.

Never fabricate validation statistics.

---

# 52. VISUAL DESIGN

The UI should look like:
> institutional research terminal + geospatial intelligence dashboard

Not:
> college assignment dashboard.

Prioritize:
* map
* evidence
* numbers
* scenario controls
* decomposition
* confidence
* sources

Avoid unnecessary decorative charts.

---

# 53. THE 5-MINUTE INTERVIEW DEMO

Design the entire application around this demonstration:

### Step 1
Select parcel.

### Step 2
Show baseline value + terrain.

### Step 3
Toggle +0.5 / +1.0 / +1.5 / +2.0m.

### Step 4
Show connected inundation and usable-land loss.

### Step 5
Turn on subsidence.

### Step 6
Show effective relative SLR.

### Step 7
Show NDVI/NDMI/NDRE temporal signals.

### Step 8
Show flood-disrupted roads.

### Step 9
Show hospital / market / highway accessibility.

### Step 10
Show risk decomposition.

### Step 11
Show uncertainty and top sensitivity drivers.

### Step 12
Show climate-adjusted valuation range.

### Step 13
Generate underwriting memo.

### Step 14
Open GitHub architecture + tests + CI.

The supplied research specifically identified this flow as a high-value interview demonstration.

---

# 54. CAREER-GAP PORTFOLIO POSITIONING

ALVERIS must demonstrate that the builder can:
* work with real geospatial data
* build beyond notebooks
* work with raster/vector/tabular/graph data
* understand data quality
* reason about physical climate risk
* connect technical outputs to financial decisions
* design APIs
* write tests
* containerize applications
* explain engineering trade-offs
* create reproducible pipelines

Do not over-focus on the career gap.

Let the repository demonstrate current ability.

---

# 55. RESUME / INTERVIEW LANGUAGE

Use language such as:
> Designed and built ALVERIS, an explainable GeoAI climate-risk underwriting platform integrating terrain analysis, scenario-based relative sea-level rise, satellite-derived ground-motion indicators, Sentinel-2 environmental stress metrics, and flood-disrupted transport-network analysis.

Never imply that the project is a licensed commercial risk model.

---

# 56. DEVELOPMENT ROADMAP

Build in stages.

## Phase 1 — Foundation
* repository
* environment
* Docker
* configuration
* PostGIS
* sample parcel
* tests
* CI

## Phase 2 — Terrain
* DEM ingestion
* clipping
* elevation statistics
* terrain features

## Phase 3 — SLR
* baseline
* +0.5
* +1
* +1.5
* +2
* connected inundation
* scenario maps

## Phase 4 — Sentinel-2
* cloud masking
* NDVI
* NDMI
* NDRE
* temporal baseline
* anomaly
* trend

## Phase 5 — Subsidence
* precomputed InSAR/VLM
* quality handling
* temporal trend
* relative SLR integration

## Phase 6 — Network
* OSMnx
* baseline routing
* flood disruption
* passability
* alternate routes
* isolation

## Phase 7 — Risk
* component scores
* composite
* confidence
* explainability

## Phase 8 — Finance
* baseline value
* scenario valuation
* sensitivity
* Climate VaR proxy

## Phase 9 — Product
* Streamlit
* FastAPI
* reporting
* portfolio view

## Phase 10 — Polish
* tests
* CI
* docs
* case studies
* demo video
* deployment

---

# 57. MVP DEFINITION

The first public release should NOT attempt everything.

Minimum impressive MVP:
```text
1 geography
10–30 parcels
coastal case
agricultural case
inland logistics case

DEM
+0.5 to +2.0m scenarios
connected inundation
Sentinel-2 NDVI/NDMI/NDRE
precomputed subsidence
OSMnx network disruption
risk score
confidence
valuation range
underwriting memo
Docker
Pytest
CI
```

This is enough for a strong public release.

---

# 58. CRITICAL “DO NOT CHEAT” RULES

Never:
* fabricate datasets
* fabricate empirical relationships
* fabricate accuracy
* fabricate validation
* claim NDVI proves soil degradation
* claim four scenarios are Monte Carlo
* assume bounding-box edges equal the ocean
* ignore CRS
* ignore vertical datum
* add subsidence twice
* use arbitrary thresholds without documentation
* remove roads without clearly defining passability assumptions
* call synthetic data observed data
* output false precision
* hide uncertainty
* hard-code proprietary-provider assumptions
* present arbitrary risk weights as scientific truth

When evidence is unavailable, surface the limitation.

---

# 59. AGENT BEHAVIOR

You have autonomy to make reasonable implementation decisions.

Do NOT repeatedly stop for trivial clarification.

When a decision is ambiguous:
1. choose the most defensible default
2. document it
3. make it configurable
4. continue implementation

Do not create fake integrations simply because a provider is named.

If an external source requires credentials:
* implement an adapter interface
* provide a documented mock/sample fixture
* clearly label it

Do not block the whole project on proprietary data.

---

# 60. RESEARCH VERIFICATION

Before implementing externally sourced data integrations or relying on current package/API behavior:
* verify current official documentation
* prefer first-party sources
* record the source URL
* record access date
* document licensing
* avoid deprecated APIs
* pin compatible package versions

Use authoritative data wherever possible.

---

# 61. DEFINITION OF DONE

ALVERIS is not “done” merely because the Streamlit app opens.

A feature is complete only when it has:
```text
Implementation
+
Tests
+
Configuration
+
Documentation
+
Metadata / lineage
+
Error handling
+
Example/demo
```

The whole system is ready for portfolio publication when:
* fresh clone works
* Docker works
* sample dataset works
* demo works
* tests pass
* CI passes
* README is complete
* architecture is documented
* assumptions are documented
* limitations are documented
* results are reproducible
* screenshots exist
* report generation works
* scenario comparison works
* uncertainty is visible
* no unsupported claims are made

---

# 62. FINAL PRODUCT TEST

Before declaring completion, perform an end-to-end run:
```text
Sample Parcel
 ↓
Ingest DEM
 ↓
Terrain Features
 ↓
SLR Scenario
 ↓
Connected Inundation
 ↓
Subsidence
 ↓
Relative SLR
 ↓
Sentinel Stress
 ↓
Network Disruption
 ↓
Risk
 ↓
Confidence
 ↓
Climate-Adjusted Valuation
 ↓
Report
 ↓
Dashboard
```

Then verify that every final metric can be traced backward.

---

# 63. FINAL PRODUCT NARRATIVE

The final application should communicate this clearly:
> ALVERIS helps investors and lenders evaluate whether a parcel's apparent market value survives physical climate risk. It combines terrain, relative sea-level-rise scenarios, land-subsidence indicators, satellite-derived environmental stress and infrastructure-network resilience to estimate climate-adjusted land usability, collateral resilience and valuation outcomes. The system is designed as a reproducible, explainable and auditable decision-support platform.

---

# 64. START NOW

Begin by:
1. Inspecting the existing repository and environment.
2. Creating an architecture and implementation plan.
3. Creating the repository structure.
4. Setting up the Python environment and dependency management.
5. Adding configuration schemas.
6. Adding sample/demo data structure.
7. Implementing the smallest vertical slice from parcel → DEM → SLR → risk → dashboard.
8. Testing that vertical slice.
9. Then iteratively add subsidence, Sentinel-2, network resilience, financial modeling, uncertainty and portfolio analytics.
10. Keep production code separate from notebooks.
11. Keep the project runnable at every milestone.

Do not build a giant monolith.
Build ALVERIS as a set of independently testable modules with clear input/output contracts.
