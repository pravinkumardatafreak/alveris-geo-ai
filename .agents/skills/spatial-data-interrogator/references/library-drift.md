# Library drift — breaking API changes

## This is a different failure class

Everything in `SKILL.md` is about **silent wrongness**: code that runs, returns
plausible output, and is false. Tier 1 and tier 2 exist because that class
gives you no signal at all — no traceback, no warning, nothing but a number
that happens to be wrong.

Version drift is the opposite. It is **loud**: an `AttributeError` or
`ImportError` on the first call, before any data is processed, with the missing
name printed in the message. It stops the program rather than corrupting the
answer.

Treat the two differently:

|  | Silent wrongness | Version drift |
|---|---|---|
| Signal | None — output looks fine | Immediate exception |
| Cost of missing it | Wrong published result | Nothing; you cannot miss it |
| Time to fix | Hours of interrogation | Minutes, mechanical |
| Where the fault is | Data, CRS, or reasoning | Environment versus code vintage |
| Tier 1 / tier 2 apply | Yes | No |

**When an `AttributeError` names one of the libraries below, it is version
drift, not your code.** The logic is fine. The environment and the code were
written against different major versions. Do not start debugging the analysis,
do not re-examine the geometry, and do not run tier 1 — fix the call and move
on.

The diagnostic question is only ever: *which version is installed, and which
version was this call written for?*

```python
import h3, osmnx, shapely, rasterio, geopandas
for m in (h3, osmnx, shapely, rasterio, geopandas):
    print(m.__name__, m.__version__)
```

---

## h3

Version 4 renamed essentially the whole API. Names lost their `h3_` prefixes
and moved to a consistent `<from>_to_<to>` scheme. Code written against v3
fails immediately on v4, and vice versa.

### `polyfill` removed in v4

```python
# v3 — fails on v4 with: AttributeError: module 'h3' has no attribute 'polyfill'
cells = h3.polyfill(geojson_dict, resolution, geo_json_conformant=True)
```

```python
# v4
poly = h3.LatLngPoly(exterior_coords)          # [(lat, lng), ...]
cells = h3.polygon_to_cells(poly, resolution)
```

Note the coordinate order: `LatLngPoly` takes **(lat, lng)**, while GeoJSON
uses **(lng, lat)**. Converting a v3 call that relied on
`geo_json_conformant=True` means swapping the pairs. Getting this wrong is a
silent failure — the cells come back, they are just in the wrong place — so
verify the result against tier 1a before trusting it.

### `get_resolution` moved

```python
# v3
res = h3.h3_get_resolution(cell)

# v4 — AttributeError: module 'h3' has no attribute 'get_resolution' means
#      you are calling the v4 name on a v3 install
res = h3.get_resolution(cell)
```

Other v3 → v4 renames in the same family, for recognising the pattern:
`geo_to_h3` → `latlng_to_cell`, `h3_to_geo` → `cell_to_latlng`,
`h3_to_geo_boundary` → `cell_to_boundary`, `k_ring` → `grid_disk`,
`h3_to_parent` → `cell_to_parent`, `h3_is_valid` → `is_valid_cell`.

---

## osmnx

### `geometries_from_place` renamed in 2.0

The `geometries_*` family became `features_*`. Deprecated through 1.9, removed
in 2.0.

```python
# fails: AttributeError: module 'osmnx' has no attribute 'geometries_from_place'
gdf = ox.geometries_from_place("Budapest, Hungary", tags={"building": True})
```

```python
# 2.0
gdf = ox.features_from_place("Budapest, Hungary", tags={"building": True})
```

Same rename across the family: `geometries_from_point` → `features_from_point`,
`geometries_from_bbox` → `features_from_bbox`,
`geometries_from_polygon` → `features_from_polygon`,
`geometries_from_address` → `features_from_address`.

### Internal module paths are not API

```python
# AttributeError: module 'osmnx.utils_geo' has no attribute 'Point'
pt = ox.utils_geo.Point(x, y)
```

`Point` is Shapely's, not osmnx's — import it from `shapely.geometry`. More
generally, osmnx reorganised its internal modules in 2.0; anything reached
through `ox.utils_*`, `ox._errors`, or another underscore-prefixed path is
private and may move between minor versions.

```python
# this import path is internal and version-fragile
from osmnx._errors import InsufficientResponseError
```

Prefer catching what the public API documents, or catch broadly and inspect,
rather than importing private exception classes.

---

## shapely

### `strtree` relocated in 2.0

```python
# AttributeError: module 'shapely' has no attribute 'strtree'
tree = shapely.strtree.STRtree(geoms)
```

The attribute error here is usually about **submodule import**, not the class
moving: `import shapely` does not bind `shapely.strtree`. In 2.0 the class is
exported at top level:

```python
from shapely import STRtree           # 2.0
tree = STRtree(geoms)
```

```python
from shapely.strtree import STRtree   # works in 1.8 and 2.0
```

Behaviour changed too, which matters more than the import: in Shapely 2.0
`STRtree.query()` returns **integer indices** into the input array, where 1.8
returned geometry objects. Code that iterates the result expecting geometries
will not raise — it will operate on integers and fail somewhere further down,
or silently produce nonsense. That makes this one a drift error that *becomes*
a silent-wrongness error if you only fix the import.

---

## rasterio

### `rasterio.plot` is not an attribute

```python
# AttributeError: module 'rasterio' has no attribute 'plot'
rasterio.plot.show(src)
```

`rasterio.plot` is an optional submodule that depends on matplotlib and is not
imported by `import rasterio`. Import it explicitly:

```python
from rasterio.plot import show
show(src)
```

The same applies to `rasterio.mask`, `rasterio.features`, and `rasterio.warp` —
all require their own import.

### `Reproject` import path in `rasterio.warp`

```python
# ImportError: cannot import name 'Reproject' from 'rasterio.warp'
from rasterio.warp import Reproject
```

There is no `Reproject` class. The function is lowercase, and the companions
usually needed with it:

```python
from rasterio.warp import reproject, calculate_default_transform, Resampling
```

`Resampling` is the enum that selects the resampling method — and choosing it
correctly for categorical versus continuous rasters is a
silent-wrongness question, not a drift question. See
`references/projection-choice.md`.

---

## geopandas

### Import failures under environment drift

```python
ModuleNotFoundError: No module named 'geopandas'
```

Rarely an actual missing install. Almost always the interpreter running the
code is not the environment where geopandas lives:

- A Jupyter kernel registered against a different environment than the one
  activated in the shell.
- An IDE using its own interpreter rather than the project environment.
- `pip install` into the system Python while the work happens in a conda
  environment, or the reverse.

Confirm which interpreter is actually executing before reinstalling anything:

```python
import sys
print(sys.executable)
print(sys.prefix)
```

Compare that path against the environment you believe you are in. Reinstalling
into the wrong environment is the usual next twenty minutes.

Geopandas also carries a heavy compiled dependency stack — GDAL, GEOS, PROJ —
and a broken install can surface as an import error mentioning one of those
rather than geopandas itself. A mismatched PROJ can also produce *wrong
transformations* rather than errors, which is a silent-wrongness case and
belongs back in tier 1.
