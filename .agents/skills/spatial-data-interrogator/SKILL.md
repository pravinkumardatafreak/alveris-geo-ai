---
name: spatial-data-interrogator
description: Diagnoses spatial analysis results that are wrong but throw no error. Use when the results look wrong, the map is off, layers don't line up, buildings are misaligned, geometries look shifted or offset, a spatial join returns nothing or too few rows, areas are wrong or off by orders of magnitude, coordinates land in the ocean or at null island, points fall in the wrong hemisphere, or there is a CRS problem or projection issue. Interrogates the data before the code — requires visual verification (plot all layers together, read the axis labels, zoom to feature scale) before applying CRS, row-count, null-geometry, and range-plausibility gates. Also covers version-drift AttributeErrors in h3, osmnx, shapely, rasterio, and geopandas. Not for writing new spatial pipelines from scratch, not for non-spatial debugging, and not for install or environment setup errors.
---

# Spatial Data Interrogator

For spatial results that are **wrong but do not raise**. A traceback tells you
where it broke. This skill is for when nothing broke and the answer is still
false: the join that returns 40% of the rows it should, the buffer measured in
degrees, the raster that lands one tile east of its vectors.

This skill interrogates data and directs attention. It does not write
pipelines.

---

## 1. The top rule

**Verify geometry by looking at it, not by reading what it says about itself.**

Metadata is an assertion, not an observation. `gdf.crs` returning `EPSG:4326`
tells you that a string is attached to the object. It does not tell you the
coordinates are longitude/latitude degrees. The two can disagree, and when they
disagree the metadata is usually the thing that is wrong — because CRS is
routinely assigned *after* coordinates have already been read, swapped,
truncated, or reprojected by something upstream.

Common ways metadata lies:

- `set_crs()` used where `to_crs()` was meant. The label changes; the
  coordinates do not move. Every downstream measurement is now silently wrong.
- A shapefile's `.prj` is missing, and a default was assumed at read time.
- Coordinates arrive as `(lat, lon)` from an API, get loaded as `(x, y)`, and
  the CRS is stamped 4326 anyway. Budapest is now in Somalia.
- A file is reprojected on disk but the sidecar metadata is stale.
- Geometry is rebuilt from a WKT column that lost its SRID.

Plotting cannot lie in this way. Pixels land where the coordinates put them.
A picture of the geometry is primary evidence; every attribute describing the
geometry is secondary. **When the two conflict, believe the picture.**

This ordering drives everything below: tier 1 is looking, tier 2 is reading.
Tier 2 never runs first.

---

## 2. Tier 1 — visual checks

Run these **before** opening the function that built the layer, before checking
join keys, before reading a single line of the pipeline. All three together
cost under a minute and eliminate the entire class of catastrophic failure.

### 1a. Plot every layer together, on one axes object

One map. All layers. Same figure.

The question is not "does this look nice", it is **"do these land in the same
window?"**

What this catches in ten seconds:

| What you see | What it means |
|---|---|
| One layer is a dot; the other is a continent | Unit mismatch — one layer in degrees, one in metres |
| Layers are in different hemispheres | Sign flip, or lon/lat swapped |
| One layer sits near (0, 0) off West Africa | Null Island — coordinates lost, defaulted to zero |
| Layers are the right shape but far apart | Different CRS, no reprojection, or `set_crs` misuse |
| One layer is mirrored or rotated 90° | Coordinate order swapped |
| A layer is empty and plots nothing | Filter or join already killed it upstream |

If the layers do not share a window, **stop**. Nothing downstream is worth
inspecting. The failure is here.

A note on how to plot: do not let a web basemap or an auto-fit viewport hide
the disagreement. An interactive map that silently reprojects everything to
Web Mercator, or an axes object that zooms to the union of both layers, can
make a catastrophic offset look like a modest one. Plot raw coordinates on
plain axes first.

### 1b. Read the axis labels

The plot has numbers on it. Read them. This is where unit confusion and
coordinate-order swaps become **numerical** rather than impressionistic.

Ask, in order:

1. **Degrees or metres?** Values in `-180..180` / `-90..90` are almost
   certainly degrees. Values in the hundreds of thousands to millions are
   projected metres. Values in the tens of millions are probably Web Mercator.
2. **Is the range plausible for the place?** A city spans roughly 0.1–0.5
   degrees, or 10,000–50,000 metres. A city spanning 300 units in a projected
   CRS is not a city.
3. **Are x and y in the right ranges relative to each other?** Latitude is
   bounded at ±90. If the y-axis exceeds 90 while x stays inside ±180, you are
   looking at either projected coordinates or a swap.
4. **Does a buffer distance make sense against this axis?** If the axis reads
   in degrees and the code buffers by `500`, the buffer is 500 degrees.

**Hide axes LAST.**

State this to the user explicitly whenever they are iterating on a map:
publication-grade cartography drops the axes, and dropping them removes the
single cheapest diagnostic available. `ax.set_axis_off()` belongs in the last
cell you run before export — never during exploration. A map that has had its
axes hidden since the first draft has been flying blind for the entire
session, and any unit error in it has been invisible the whole time.

### 1c. Go interactive, zoom to feature scale

Static full-extent views hide small errors. A 30-metre offset across a whole
city is roughly one pixel. Zoomed to a single building it is unmistakable.

Switch to an interactive map with toggleable layers and zoom until individual
features are legible — building footprints, road centrelines, parcel edges.

What only appears at this scale:

- **Datum shift** — a consistent offset of a few metres to tens of metres in
  one direction, everywhere. Typically an ellipsoid or datum mismatch, not a
  CRS code mismatch. Both layers claim to be "in WGS84" and both are, sort of.
- **Resampling artifacts** — raster edges that stair-step against vector
  boundaries, or a categorical raster that has acquired interpolated values
  along class boundaries that exist in no legend.
- **Half-pixel registration errors** — raster shifted by exactly half a cell,
  from a transform built on cell centres versus cell corners.
- **Snapping and precision loss** — vertices collapsed onto a coarse grid by a
  round-trip through a low-precision format.
- **Partial alignment** — one part of the extent lines up and another does not,
  which points at a warp or a mosaic seam rather than a global transform error.

Toggle layers on and off against each other. A shift that is invisible when
both layers are drawn is obvious when you flick between them.

---

## 3. Tier 2 — code gates

**Only once tier 1 looks right.** If layers do not share a window, these gates
will pass cleanly on data that is already ruined.

These are diagnostic checks, not pipeline code. They print and assert; they do
not transform.

### Gate 1 — Print CRS before and after every transform

Every reprojection, every read, every geometry rebuild. Not "at the start" —
around each operation, so the step that changed it is identifiable.

Also check the *coordinates*, not just the label: print the bounds alongside
the CRS. A CRS that changed while the bounds did not is `set_crs` where
`to_crs` was meant. Bounds that changed while the CRS did not is a transform
applied without relabelling.

### Gate 2 — Row accounting on every join and filter

Record in-count and out-count for each. A spatial join is the single most
common place for silent loss, and `sjoin` returning fewer rows is not an
error condition — it is the documented behaviour of an inner join.

Three numbers matter: left rows in, right rows in, rows out. Then:

- **Out == 0** — no spatial relationship at all. Almost always mismatched CRS,
  which tier 1 should already have caught. If tier 1 was clean, check the
  predicate (`within` vs `intersects` vs `contains`) and the geometry types.
- **Out < left** — unmatched left rows were dropped. Decide deliberately
  whether that is correct, and switch to a left join if it is not.
- **Out > left** — one left feature matched several right features. Duplicated
  rows now inflate every downstream sum and count. This is the failure mode
  that produces plausible-looking totals that are 1.4× too large.

### Gate 3 — Null and invalid geometry check before anything downstream

Count `.geometry.isna()` and `(~.geometry.is_valid)` before any operation that
consumes geometry. Nulls propagate quietly through joins and dissolve; invalid
self-intersecting polygons produce area and intersection results that are
wrong rather than absent.

Do this at read time and again after any operation that constructs geometry.

### Gate 4 — Range plausibility in the stated units

For every computed measure, state the expected magnitude *before* looking at
the result, then compare.

- Areas of urban parcels: hundreds to thousands of m².
- Building heights: single digits to low hundreds of metres.
- Population density: hundreds to tens of thousands per km².
- Distances between adjacent features: metres, not degrees, not millions.

A result in the right *shape* but wrong by three to five orders of magnitude is
the signature of a degrees-versus-metres error. Off by ~111,000 in one
direction points at a degree/metre conversion at the equator. Off by a factor
that varies with latitude points at Web Mercator area distortion — Mercator is
conformal, not equal-area, and areas computed in EPSG:3857 are wrong everywhere
except the equator and increasingly wrong toward the poles.

### Gate 5 — One hand-checkable unit

Take a single feature. One building, one tract, one point. Verify it manually,
end to end, against an external reference: measure it on a basemap, look up the
known value, check the coordinate in a separate tool.

This is the gate that catches errors the aggregate statistics hide. A pipeline
can produce a distribution with an entirely plausible mean, median, and spread
while every single value is wrong by the same factor. One hand-checked feature
falsifies that in a minute.

---

## 4. How this skill opens a request

**Procedure, not policy.** The first response to a diagnosis request is not a
pipeline. It is tier 1, handed back to the user as two or three concrete things
to look at, with a request to describe what they see.

The reason is diagnostic, not procedural caution: a pipeline written before the
geometry has been looked at encodes whatever is already wrong with the data. If
the layers are in mismatched CRSs, code built on top of them produces confident,
well-formatted, wrong output — and now the error is buried under a working
program instead of sitting on the surface.

So: ask for the picture first. Then proceed with everything the picture allows.

Once the user reports back, move immediately to tier 2 and the actual work. Do
not ask for a second round of looking unless their answer revealed a tier 1
failure.

---

## 5. Routing

Every diagnosis ends by naming the lesson that covers the underlying concept.
Name and link it; **never reproduce its content here.** The diagnosis says what
went wrong and what to change. The lesson says why, and it is the lesson's job.

Routing table:

| Diagnosis | Route to |
|---|---|
| Layers in different windows, CRS mismatch | `references/projection-choice.md` |
| `set_crs` used where `to_crs` was meant | `references/projection-choice.md` |
| Coordinates at (0, 0) or in the wrong hemisphere | `references/projection-choice.md` |
| Buffer or distance in degrees | `references/projection-choice.md` |
| Areas wrong by a latitude-dependent factor | `references/projection-choice.md` |
| Small persistent offset at building scale | `references/projection-choice.md` |
| Raster misaligned by a fraction of a cell | `references/projection-choice.md` |
| Categorical raster with invented class values | `references/projection-choice.md` |
| Spatial join returning zero rows | `references/projection-choice.md` |
| Spatial join inflating row counts | `references/projection-choice.md` |
| Null or invalid geometry propagating downstream | `references/projection-choice.md` |
| Aggregates plausible, individual values wrong | `references/projection-choice.md` |
| `AttributeError` naming a spatial library | See `references/library-drift.md` — version drift, not this skill |

---

## References

- `references/library-drift.md` — breaking API changes in h3, osmnx, shapely,
  rasterio, geopandas. A **loud** failure class, distinct from everything above.
- `references/projection-choice.md` — projection selection, resampling choice,
  and criteria for rejecting a join.
