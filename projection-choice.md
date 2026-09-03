# Projection choice, resampling, and join rejection

> **Skeleton.** Structure only — content marked `[[FILL]]` is to be written by
> the skill author. Do not populate these from general knowledge; the point of
> this file is to encode one specific set of rules, not the average of all
> advice on the topic.

---

## 1. Projection by latitude band and analysis type

Selection rule keyed on two inputs: where the data is, and what is being
measured.

### 1.1 By latitude band

| Band | Projection | Notes |
|---|---|---|
| Equatorial (0°–15°) | [[FILL]] | [[FILL]] |
| Low mid-latitude (15°–35°) | [[FILL]] | [[FILL]] |
| High mid-latitude (35°–55°) | [[FILL]] | [[FILL]] |
| Sub-polar (55°–70°) | [[FILL]] | [[FILL]] |
| Polar (>70°) | [[FILL]] | [[FILL]] |

### 1.2 By analysis type

| Analysis | Requirement | Projection | Notes |
|---|---|---|---|
| Area / density | [[FILL]] | [[FILL]] | [[FILL]] |
| Distance / buffering | [[FILL]] | [[FILL]] | [[FILL]] |
| Shape / angle / direction | [[FILL]] | [[FILL]] | [[FILL]] |
| Network / routing | [[FILL]] | [[FILL]] | [[FILL]] |
| Visualisation only | [[FILL]] | [[FILL]] | [[FILL]] |

### 1.3 Extent-driven overrides

When extent, rather than latitude or analysis type, forces the choice.

- Single city / metro: [[FILL]]
- Single country: [[FILL]]
- Continental: [[FILL]]
- Global: [[FILL]]
- Crossing a UTM zone boundary: [[FILL]]
- Crossing the antimeridian: [[FILL]]

### 1.4 Defaults and when to override them

- Default working CRS: [[FILL]]
- Default for measurement: [[FILL]]
- Default for output / delivery: [[FILL]]
- Conditions that override the default: [[FILL]]

---

## 2. Equal-area vs equal-distance vs conformal

No projection preserves all three. This section records which property to
protect for which question, and what the cost is.

### 2.1 What each property preserves and destroys

| Property | Preserves | Distorts | Choose when |
|---|---|---|---|
| Equal-area | [[FILL]] | [[FILL]] | [[FILL]] |
| Equidistant | [[FILL]] | [[FILL]] | [[FILL]] |
| Conformal | [[FILL]] | [[FILL]] | [[FILL]] |
| Compromise | [[FILL]] | [[FILL]] | [[FILL]] |

### 2.2 When the choice materially changes the answer

Cases where picking wrong produces a *different conclusion*, not just a
slightly different number.

- [[FILL]]
- [[FILL]]
- [[FILL]]

### 2.3 Web Mercator specifically

- Acceptable uses: [[FILL]]
- Prohibited uses: [[FILL]]
- Magnitude of area error by latitude: [[FILL]]
- How this shows up in results: [[FILL]]

### 2.4 Tolerance thresholds

How much distortion is acceptable before the projection must change.

| Measure | Threshold | Action if exceeded |
|---|---|---|
| Area error | [[FILL]] | [[FILL]] |
| Distance error | [[FILL]] | [[FILL]] |
| Angular error | [[FILL]] | [[FILL]] |

---

## 3. Resampling method by raster type

The choice is determined by whether pixel values are **categories** or
**measurements**. Interpolating a category invents classes that exist in no
legend.

### 3.1 Categorical rasters

Land cover, class labels, zone IDs, masks.

- Permitted methods: [[FILL]]
- Forbidden methods: [[FILL]]
- Why: [[FILL]]
- How the failure appears in output: [[FILL]]

### 3.2 Continuous rasters

Elevation, reflectance, temperature, indices.

- Default method: [[FILL]]
- When to use a higher-order method: [[FILL]]
- When to use a lower-order method: [[FILL]]
- Edge and no-data handling: [[FILL]]

### 3.3 Upsampling vs downsampling

| Direction | Categorical | Continuous |
|---|---|---|
| Upsample (finer) | [[FILL]] | [[FILL]] |
| Downsample (coarser) | [[FILL]] | [[FILL]] |

Aggregation choice when downsampling continuous data (mean / median / max /
mode): [[FILL]]

### 3.4 Alignment and registration

- Target grid definition: [[FILL]]
- Cell-centre vs cell-corner convention: [[FILL]]
- Snapping tolerance: [[FILL]]
- Acceptable residual offset: [[FILL]]

### 3.5 Mixed-resolution stacks

Rule for which layer sets the target resolution when combining sources:
[[FILL]]

---

## 4. Criteria for rejecting a join outright

Conditions under which the correct action is to **refuse the join** rather than
run it and caveat the result.

### 4.1 Hard rejections

Fail immediately; do not proceed with a warning.

| Condition | Rationale |
|---|---|
| [[FILL]] | [[FILL]] |
| [[FILL]] | [[FILL]] |
| [[FILL]] | [[FILL]] |

### 4.2 Match-rate thresholds

| Match rate | Verdict | Action |
|---|---|---|
| [[FILL]] | [[FILL]] | [[FILL]] |
| [[FILL]] | [[FILL]] | [[FILL]] |
| [[FILL]] | [[FILL]] | [[FILL]] |

### 4.3 Geometry-quality preconditions

Checks that must pass *before* a join is attempted at all.

- [[FILL]]
- [[FILL]]
- [[FILL]]

### 4.4 Semantic mismatches

Cases where the geometries relate correctly but the join is still meaningless
— resolution mismatch, temporal mismatch, incompatible units of observation.

- [[FILL]]
- [[FILL]]
- [[FILL]]

### 4.5 Predicate selection

| Predicate | Use when | Common misuse |
|---|---|---|
| `intersects` | [[FILL]] | [[FILL]] |
| `within` | [[FILL]] | [[FILL]] |
| `contains` | [[FILL]] | [[FILL]] |
| `nearest` | [[FILL]] | [[FILL]] |

### 4.6 What to report when rejecting

Required content of a rejection message to the user: [[FILL]]
