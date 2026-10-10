"""2D Earth Observation raster heatmap visualizers for ALVERIS.

Implements high-fidelity scientific raster visualizers:
- Copernicus GLO-30 DEM elevation grids with topographic contours.
- Horn's slope surface gradient maps (degrees).
- Sentinel-2 Level-2A False-Color Infrared (CIR) canopy reflectance imagery.
- InSAR multi-decadal subsidence deformation field.
"""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")  # Non-interactive backend for headless Streamlit / CI


plt.style.use("dark_background")


def plot_dem_elevation_raster(
    elevation_grid: np.ndarray,
    water_level_rise_m: float = 0.0,
) -> plt.Figure:
    """Render high-contrast 2D DEM elevation raster with topographic contours."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    fig.patch.set_facecolor("#0b121e")
    ax.set_facecolor("#0b121e")

    valid_data = elevation_grid[~np.isnan(elevation_grid)]
    vmin = float(np.percentile(valid_data, 2)) if len(valid_data) > 0 else 0.0
    vmax = float(np.percentile(valid_data, 98)) if len(valid_data) > 0 else 10.0
    if vmin >= vmax:
        vmax = vmin + 1.0

    im = ax.imshow(elevation_grid, cmap="terrain", origin="upper", vmin=vmin, vmax=vmax)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Elevation (m above MSL)", color="#e2e8f0", fontsize=9)
    cbar.ax.tick_params(colors="#cbd5e1", labelsize=8)

    # Topographic contour overlay
    contours = ax.contour(
        elevation_grid,
        levels=6,
        colors="#ffffff",
        alpha=0.35,
        linewidths=0.8,
    )
    ax.clabel(contours, inline=True, fontsize=7, fmt="%.1fm")

    # Sea level breach contour if water level rises above vmin
    if vmin <= water_level_rise_m <= vmax:
        ax.contour(
            elevation_grid,
            levels=[water_level_rise_m],
            colors="#00e5ff",
            linewidths=2.0,
            linestyles="--",
        )

    ax.set_title(
        f"Copernicus DEM (SLR Breach: {water_level_rise_m:+.1f}m MSL)",
        color="#f8fafc",
        fontsize=11,
        weight="bold",
        pad=10,
    )
    ax.set_xlabel("Easting Grid Pixel", color="#94a3b8", fontsize=9)
    ax.set_ylabel("Northing Grid Pixel", color="#94a3b8", fontsize=9)
    ax.tick_params(colors="#64748b", labelsize=8)
    fig.tight_layout()
    return fig


def plot_slope_gradient_raster(slope_degrees: np.ndarray) -> plt.Figure:
    """Render Horn's 8-neighbor surface slope gradient map in degrees."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    fig.patch.set_facecolor("#0b121e")
    ax.set_facecolor("#0b121e")

    vmax = float(max(5.0, np.nanpercentile(slope_degrees, 95)))
    im = ax.imshow(slope_degrees, cmap="YlOrRd", origin="upper", vmin=0.0, vmax=vmax)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Terrain Slope (degrees)", color="#e2e8f0", fontsize=9)
    cbar.ax.tick_params(colors="#cbd5e1", labelsize=8)

    ax.set_title(
        "Horn's Surface Slope Gradient (Topographic Drainage)",
        color="#f8fafc",
        fontsize=11,
        weight="bold",
        pad=10,
    )
    ax.set_xlabel("Easting Grid Pixel", color="#94a3b8", fontsize=9)
    ax.set_ylabel("Northing Grid Pixel", color="#94a3b8", fontsize=9)
    ax.tick_params(colors="#64748b", labelsize=8)
    fig.tight_layout()
    return fig


def plot_sentinel2_false_color_cir(tensor_data: np.ndarray) -> plt.Figure:
    """Render Sentinel-2 Level-2A False-Color Infrared (CIR: NIR, Red, Green)."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    fig.patch.set_facecolor("#0b121e")
    ax.set_facecolor("#0b121e")

    # In ALVERIS tensors: B0=Blue, B1=Green, B2=Red, B3=NIR
    # Standard Color Infrared (CIR): R=NIR (B3), G=Red (B2), B=Green (B1)
    if tensor_data.shape[0] >= 4:
        nir = tensor_data[3].astype(np.float32)
        red = tensor_data[2].astype(np.float32)
        green = tensor_data[1].astype(np.float32)
    else:
        nir = tensor_data[0].astype(np.float32)
        red = tensor_data[0].astype(np.float32)
        green = tensor_data[0].astype(np.float32)

    def _norm(band: np.ndarray) -> np.ndarray:
        p2, p98 = np.percentile(band, 2), np.percentile(band, 98)
        if p98 <= p2:
            return np.clip(band, 0.0, 1.0)
        return np.clip((band - p2) / (p98 - p2), 0.0, 1.0)

    rgb = np.stack([_norm(nir), _norm(red), _norm(green)], axis=-1)
    ax.imshow(rgb, origin="upper")

    ax.set_title(
        "Sentinel-2 CIR (Red=Healthy Canopy, Cyan=Water/Pavement)",
        color="#f8fafc",
        fontsize=11,
        weight="bold",
        pad=10,
    )
    ax.set_xlabel("Easting Grid Pixel", color="#94a3b8", fontsize=9)
    ax.set_ylabel("Northing Grid Pixel", color="#94a3b8", fontsize=9)
    ax.tick_params(colors="#64748b", labelsize=8)
    fig.tight_layout()
    return fig


def plot_insar_subsidence_surface(
    mean_rate_mm: float,
    differential_gradient: float,
    shape: tuple[int, int] = (25, 25),
) -> plt.Figure:
    """Render spatial InSAR subsidence velocity field with differential settlement."""
    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    fig.patch.set_facecolor("#0b121e")
    ax.set_facecolor("#0b121e")

    rows, cols = shape
    y_coords, x_coords = np.mgrid[:rows, :cols]
    # Simulate realistic tilt gradient across parcel
    deformation = (
        mean_rate_mm
        + (y_coords - rows / 2) * (differential_gradient * 5.0)
        + (x_coords - cols / 2) * (differential_gradient * 3.0)
    )

    im = ax.imshow(deformation, cmap="coolwarm_r", origin="upper")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Subsidence Velocity (mm / year)", color="#e2e8f0", fontsize=9)
    cbar.ax.tick_params(colors="#cbd5e1", labelsize=8)

    ax.set_title(
        f"InSAR Deformation Surface ({mean_rate_mm:.1f} mm/yr ± {differential_gradient:.2f})",
        color="#f8fafc",
        fontsize=11,
        weight="bold",
        pad=10,
    )
    ax.set_xlabel("Easting Grid Pixel", color="#94a3b8", fontsize=9)
    ax.set_ylabel("Northing Grid Pixel", color="#94a3b8", fontsize=9)
    ax.tick_params(colors="#64748b", labelsize=8)
    fig.tight_layout()
    return fig
