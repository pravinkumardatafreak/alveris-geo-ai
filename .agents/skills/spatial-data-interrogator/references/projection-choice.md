# Projection choice, resampling, and join rejection

## 1. Projection by latitude band and analysis type

Selection rule keyed on two inputs: where the data is, and what is being
measured.

### 1.1 By latitude band

| Band | Projection | Notes |
|---|---|---|
| Equatorial (0°–15°) | UTM Zone or Equidistant Cylindrical / WGS 84 / World Equidistant Cylindrical | Minimal distortion near equator; UTM provides planar meters |
| Low mid-latitude (15°–35°) | Local UTM Zone (e.g. UTM Zone 44N / EPSG:32644 for Tamil Nadu/Chennai) | Conformal local UTM minimises scale and angular distortion locally |
| High mid-latitude (35°–55°) | Lambert Conformal Conic (LCC) or Albers Equal Area (AEA) | Standard regional mapping projections preserving conformal or equal-area properties |
| Sub-polar (55°–70°) | Polar Stereographic or regional Lambert | Prevents high-latitude linear stretch |
| Polar (>70°) | Universal Polar Stereographic (UPS) | Standard polar projection |

### 1.2 By analysis type

| Analysis | Requirement | Projection | Notes |
|---|---|---|---|
| Area / density | Equal-area | Albers Equal Area, Sinusoidal, or local equal-area | Never use Web Mercator (EPSG:3857) or unprojected WGS84 (EPSG:4326) |
| Distance / buffering | Equidistant or local conformal planar | Local UTM Zone or Equidistant Conic | Buffer radii in metres require planar metric coordinates |
| Shape / angle / direction | Conformal | Local UTM or Lambert Conformal Conic | Preserves infinitesimal angles |
| Network / routing | Planar metric (Euclidean edge lengths) | Local UTM Zone | Preserves network edge lengths and routing distances |
| Visualisation only | Web mapping tiles | Web Mercator (EPSG:3857) | Acceptable ONLY for display/slippy map tiles, never for metric calculations |

### 1.3 Extent-driven overrides

When extent, rather than latitude or analysis type, forces the choice:

- **Single city / metro / parcel**: Local UTM Zone (e.g. EPSG:32644).
- **Single country (large)**: National grid or Albers Equal Area (e.g., India Albers Equal Area EPSG:7755).
- **Continental**: Continental equal-area (e.g. Europe Albers EPSG:3035).
- **Global**: Equal Earth (EPSG:8857) or Mollweide for equal-area displays.
- **Crossing a UTM zone boundary**: Regional LCC/Albers or adjacent-zone projection with documented boundary error.
- **Crossing the antimeridian**: Pacific-centred projection (e.g., EPSG:3832).

### 1.4 Defaults and when to override them

- **Default working CRS**: Local UTM projection (e.g., EPSG:32644 for Tamil Nadu).
- **Default for measurement**: Local UTM or national equal-area.
- **Default for output / delivery**: GeoJSON in EPSG:4326 (WGS84) per RFC 7946, with explicit CRS metadata.
- **Conditions that override the default**: Regional analyses spanning >6° of longitude override single UTM zone with regional equal-area projection.

---

## 2. Equal-area vs equal-distance vs conformal

No projection preserves all three. This section records which property to
protect for which question, and what the cost is.

### 2.1 What each property preserves and destroys

| Property | Preserves | Distorts | Choose when |
|---|---|---|---|
| Equal-area | Surface area ratios everywhere | Angles, shapes, local distances | Computing parcel area, inundated area fraction, vegetative density |
| Equidistant | Distances along specific lines/radii | Areas and shapes | Measuring radius buffers from a single reference point |
| Conformal | Local shapes, infinitesimal angles | Scale and area globally | Navigation, routing networks, local topographic slope |
| Compromise | Neither completely; balances both | Slight distortion in all | Thematic global visual maps |

### 2.2 When the choice materially changes the answer

Cases where picking wrong produces a *different conclusion*, not just a
slightly different number:

1. **Inundation Area on Web Mercator (EPSG:3857)**: Area is scaled by $1 / \cos^2(\text{lat})$. At 60° latitude, areas are inflated by 400% (4×). Even at 13°N (Chennai), areas are inflated by ~5.2%.
2. **Buffer in Unprojected WGS84 (EPSG:4326)**: `gdf.buffer(500)` creates a buffer of 500 degrees, enveloping the entire globe.
3. **Slope on Degree Grids**: Calculating terrain gradient $\Delta z / \Delta d$ when $z$ is in meters and horizontal coordinates are in degrees causes slope to be off by five orders of magnitude (~111,000×).

### 2.3 Web Mercator specifically

- **Acceptable uses**: Basemap display, slippy map rendering in Streamlit/Leaflet.
- **Prohibited uses**: Area calculations, flood extent area, buffer operations, network distance calculations, slope calculation.

---

## 3. Resampling method by raster type

The choice is determined by whether pixel values are **categories** or
**measurements**. Interpolating a category invents classes that exist in no
legend.

### 3.1 Categorical rasters

Land cover (e.g. WorldCover), class labels, zone IDs, flood extent masks (0/1).

- **Permitted methods**: `nearest` (Nearest Neighbour).
- **Forbidden methods**: `bilinear`, `cubic`, `lanczos`, `average`.
- **Why**: Bilinear interpolation between class 1 (Water) and class 3 (Urban) generates floating values like 1.8 or 2 (Vegetation), creating phantom features.
- **How the failure appears in output**: Non-existent class IDs appear along boundary pixels.

### 3.2 Continuous rasters

Elevation (DEM), reflectance bands (Sentinel-2 B02-B12), temperature, spectral indices (NDVI).

- **Default method**: `bilinear` (for continuous surfaces) or `cubic` / `cubicspline` (for smooth terrain).
- **Edge and no-data handling**: Preserve explicit nodata masks; ensure nodata is not averaged into valid cells.

### 3.3 Upsampling vs downsampling

| Direction | Categorical | Continuous |
|---|---|---|
| Upsample (finer) | `nearest` | `bilinear` or `cubicspline` |
| Downsample (coarser) | `mode` or `nearest` | `average`, `bilinear`, or `med` |

---

## 4. Criteria for rejecting a join outright

Conditions under which the correct action is to **refuse the join** rather than
run it and caveat the result.

### 4.1 Hard rejections

| Condition | Rationale |
|---|---|
| Incompatible / missing CRS | Joining unprojected (degrees) with projected (meters) produces empty or garbage matches |
| Both layers have null or invalid geometry | Invalid polygons generate GEOS topology exceptions or silent loss |
| Completely disjoint bounding boxes | When bounds show 0 spatial overlap, join will return 0 rows |

### 4.2 Match-rate thresholds

| Match rate | Verdict | Action |
|---|---|---|
| 0% matched | Hard failure | Halt pipeline; trigger Tier 1 visual CRS check |
| < 50% matched on expected 1:1 join | High alert | Log warning; verify whether features are truly out-of-bounds or dropped by predicate |
| > 100% matched (row count inflation) | One-to-many explosion | Halt or group by unique key before aggregating to prevent duplicate summation |

### 4.3 Semantic mismatches

- **Resolution mismatch**: Joining 10m parcel vectors against 100km climate grid without downscaling or explicit uncertainty bounds.
- **Temporal mismatch**: Evaluating 2026 infrastructure network with 2005 flood boundaries without noting temporal discontinuity.
