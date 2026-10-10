"""Sample DEM and spatial fixture generator for ALVERIS.

Generates realistic, physically grounded synthetic DEM rasters, ocean masks,
InSAR subsidence grids, Sentinel-2 reflectance bands, and road network graphs
for local testing, CI pipelines, and self-contained portfolio demonstrations
per Section 40 and Section 48 of the Master Specification.
"""

from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import rasterio
from rasterio.transform import from_bounds


def _compute_elevation_surface(
    shape: tuple[int, int],
    slope_gradient_m: float,
    base_elevation_m: float = 0.3,
) -> np.ndarray:
    """Compute 2D synthetic elevation surface with relief and channel cut."""
    height, width = shape
    x_norm = np.linspace(1.0, 0.0, width)
    y_norm = np.linspace(0.0, 1.0, height)
    xx, yy = np.meshgrid(x_norm, y_norm)

    elevation = xx * slope_gradient_m + base_elevation_m
    channel_path = 0.5 + 0.15 * np.sin(yy * np.pi * 3)
    channel_dist = np.abs(xx - channel_path)
    channel_cut = np.exp(-(channel_dist**2) / 0.01) * 1.5
    elevation = np.maximum(0.1, elevation - channel_cut)

    np.random.seed(42)
    roughness = np.random.normal(0.0, 0.08, size=(height, width)).astype(np.float32)
    return (elevation + roughness).astype(np.float32)


def generate_dem_for_bounds(
    output_path: str | Path,
    bounds_wgs84: tuple[float, float, float, float],
    shape: tuple[int, int] = (100, 100),
    slope_gradient_m: float = 3.5,
    base_elevation_m: float = 0.3,
) -> Path:
    """Generate a realistic synthetic DEM GeoTIFF covering specified WGS84 bounds."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    minx, miny, maxx, maxy = bounds_wgs84
    height, width = shape
    transform = from_bounds(minx, miny, maxx, maxy, width, height)
    elevation = _compute_elevation_surface(
        shape=shape,
        slope_gradient_m=slope_gradient_m,
        base_elevation_m=base_elevation_m,
    )

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=np.float32,
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999.0,
    ) as dst:
        dst.write(elevation, 1)

    return path


def generate_coastal_dem_fixture(
    output_path: str | Path,
    bounds_wgs84: tuple[float, float, float, float] = (80.30, 13.23, 80.33, 13.26),
    width: int = 100,
    height: int = 100,
    slope_gradient_m: float = 3.5,
) -> Path:
    """Generate a realistic coastal elevation GeoTIFF with estuarine relief."""
    return generate_dem_for_bounds(
        output_path=output_path,
        bounds_wgs84=bounds_wgs84,
        shape=(height, width),
        slope_gradient_m=slope_gradient_m,
        base_elevation_m=0.3,
    )


def get_or_generate_dem_for_parcel(
    parcel_geometry_wgs84: dict[str, Any],
    asset_id: str,
    output_dir: str | Path = "data/sample",
    buffer_deg: float = 0.02,
) -> Path:
    """Ensure a DEM covering the exact parcel bounding box exists on disk."""
    out_dir = Path(output_dir)
    dem_path = out_dir / f"dem_{asset_id}.tif"
    if dem_path.exists():
        return dem_path

    coords = parcel_geometry_wgs84["coordinates"][0]
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    bounds = (
        min(xs) - buffer_deg,
        min(ys) - buffer_deg,
        max(xs) + buffer_deg,
        max(ys) + buffer_deg,
    )

    if "AG" in asset_id:
        base_elev = 14.0
        slope = 5.0
    elif "LG" in asset_id:
        base_elev = 38.0
        slope = 7.5
    else:
        base_elev = 0.5
        slope = 3.5

    return generate_dem_for_bounds(
        output_path=dem_path,
        bounds_wgs84=bounds,
        slope_gradient_m=slope,
        base_elevation_m=base_elev,
    )


def generate_ocean_seed_mask(
    dem_shape: tuple[int, int],
    seed_boundary: str = "east",
) -> np.ndarray:
    """Generate an explicit ocean boundary seed mask (e.g. eastern coastal edge)."""
    mask = np.zeros(dem_shape, dtype=bool)
    if seed_boundary == "east":
        mask[:, -3:] = True
    elif seed_boundary == "west":
        mask[:, :3] = True
    elif seed_boundary == "south":
        mask[-3:, :] = True
    elif seed_boundary == "north":
        mask[:3, :] = True
    return mask


def generate_subsidence_grid_fixture(
    grid_shape: tuple[int, int],
    base_rate_mm_yr: float = 10.0,
    gradient_axis: str = "x",
) -> np.ndarray:
    """Generate a synthetic InSAR annual ground subsidence rate grid in mm/year."""
    height, width = grid_shape
    if gradient_axis == "x":
        gradient = np.linspace(0.5, 1.5, width)[np.newaxis, :]
        base = np.repeat(gradient, height, axis=0)
    else:
        gradient = np.linspace(0.5, 1.5, height)[:, np.newaxis]
        base = np.repeat(gradient, width, axis=1)

    np.random.seed(42)
    noise = np.random.normal(0.0, 0.5, size=grid_shape)
    rate_grid = (base_rate_mm_yr * base + noise).astype(np.float32)
    return np.maximum(0.0, rate_grid)


def generate_sentinel2_bands_fixture(
    grid_shape: tuple[int, int],
    condition: str = "healthy",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate synthetic Sentinel-2 L2A BOA reflectance grids (B4, B5, B8, B11)."""
    np.random.seed(42)
    noise = np.random.normal(0.0, 0.01, size=grid_shape).astype(np.float32)

    if condition == "healthy":
        b4_red = np.full(grid_shape, 0.06, dtype=np.float32) + noise
        b5_red_edge = np.full(grid_shape, 0.18, dtype=np.float32) + noise
        b8_nir = np.full(grid_shape, 0.45, dtype=np.float32) + noise
        b11_swir1 = np.full(grid_shape, 0.15, dtype=np.float32) + noise
    else:
        b4_red = np.full(grid_shape, 0.18, dtype=np.float32) + noise
        b5_red_edge = np.full(grid_shape, 0.22, dtype=np.float32) + noise
        b8_nir = np.full(grid_shape, 0.24, dtype=np.float32) + noise
        b11_swir1 = np.full(grid_shape, 0.28, dtype=np.float32) + noise

    return (
        np.clip(b4_red, 0.01, 1.0),
        np.clip(b5_red_edge, 0.01, 1.0),
        np.clip(b8_nir, 0.01, 1.0),
        np.clip(b11_swir1, 0.01, 1.0),
    )


def generate_sample_road_network_fixture() -> nx.Graph:
    """Generate a realistic local road network connecting a parcel to an arterial highway.

    Topological layout:
    - Node 0: Parcel Access Gate
    - Node 1: Coastal Low-Lying Arterial Junction
    - Node 2: Inland Regional Highway (Evacuation destination)
    - Node 3: Elevated Inland Secondary Bypass
    """
    g = nx.Graph()
    g.add_node(0, name="Parcel Gate", pos=(80.315, 13.245))
    g.add_node(1, name="Coastal Arterial Jct", pos=(80.325, 13.245))
    g.add_node(2, name="Regional Highway Hub", pos=(80.330, 13.255))
    g.add_node(3, name="Inland Bypass Jct", pos=(80.310, 13.250))

    # Edges: length in meters
    g.add_edge(0, 1, length=500.0, name="Access Spur Road", highway="residential")
    g.add_edge(1, 2, length=1000.0, name="Coastal Direct Arterial", highway="primary")
    g.add_edge(0, 3, length=800.0, name="Inland Connector", highway="secondary")
    g.add_edge(3, 2, length=1500.0, name="Elevated Inland Bypass", highway="secondary")

    return g
