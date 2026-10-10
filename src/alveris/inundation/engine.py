"""Hydrologically connected inundation engine and sea-level rise scenario processor.

Implements Phase 4 of ALVERIS:
- Level 1: Bathtub elevation screening.
- Level 2: 8-way / 4-way hydrologic connectivity with explicit sea/estuary seed masks.
- Effective elevation adjustment under land subsidence:
    EffectiveElevation = Elevation0 - Subsidence
    FloodDepth = ScenarioWaterLevel - EffectiveElevation
- Parcel-level flood outputs: flooded area, usable land loss, depth statistics,
  and identification of unconnected low-lying depressions (dry topographic pockets).
"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field
from scipy.ndimage import generate_binary_structure, label

from alveris.core.lineage import DerivedFeatureLineage


class InundationScenarioResult(BaseModel):
    """Parcel-level inundation impact metrics under a specific SLR scenario."""

    scenario_id: str = Field(..., description="Scenario identifier (e.g. 'slr_1_0').")
    water_level_rise_m: float = Field(
        ..., description="Relative sea-level rise increment in meters."
    )
    total_parcel_area_sqm: float = Field(
        ..., gt=0.0, description="Total parcel area in m²."
    )
    flooded_area_sqm: float = Field(
        ..., ge=0.0, description="Hydrologically connected flooded area in m²."
    )
    flooded_percent: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of parcel area inundated."
    )
    usable_land_loss_sqm: float = Field(
        ..., ge=0.0, description="Directly submerged land deemed economically unusable."
    )
    connected_inundation_fraction: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of parcel inundated (0.0 to 1.0)."
    )
    flood_depth_mean_m: float = Field(
        default=0.0, ge=0.0, description="Mean water depth over inundated cells in meters."
    )
    flood_depth_p90_m: float = Field(
        default=0.0, ge=0.0, description="90th percentile water depth in meters."
    )
    max_flood_depth_m: float = Field(
        default=0.0, ge=0.0, description="Maximum water depth in meters."
    )
    unconnected_low_pocket_count: int = Field(
        default=0,
        description="Low cells below water level protected from flooding by topography.",
    )
    lineage: DerivedFeatureLineage = Field(
        ..., description="Provenance describing connectivity rules and scenario."
    )


@dataclass(frozen=True)
class ScenarioParameters:
    """Configurable scenario evaluation parameters."""

    water_level_rise_m: float
    pixel_area_sqm: float
    scenario_id: str = "slr_1_0"
    subsidence_grid_m: np.ndarray | None = None


@dataclass(frozen=True)
class DepthStatistics:
    """Descriptive statistics for water depth over inundated cells."""

    depth_mean: float
    depth_p90: float
    depth_max: float


@dataclass(frozen=True)
class ParcelFloodSummary:
    """Aggregated parcel flood footprint metrics."""

    total_area_sqm: float
    flooded_area_sqm: float
    flooded_percent: float
    flooded_fraction: float
    unconnected_count: int
    depth_stats: DepthStatistics


def _compute_depth_statistics(
    depth_grid: np.ndarray, flooded_mask: np.ndarray, flooded_count: int
) -> DepthStatistics:
    """Calculate mean, p90, and max water depths on flooded cells."""
    if flooded_count > 0:
        depths = depth_grid[flooded_mask]
        return DepthStatistics(
            depth_mean=float(np.mean(depths)),
            depth_p90=float(np.percentile(depths, 90)),
            depth_max=float(np.max(depths)),
        )
    return DepthStatistics(depth_mean=0.0, depth_p90=0.0, depth_max=0.0)


def _build_inundation_lineage(
    scenario_id: str, connectivity_mode: str
) -> DerivedFeatureLineage:
    """Build provenance record for a connected flood simulation."""
    return DerivedFeatureLineage(
        feature_name=f"inundation_{scenario_id}",
        source_dataset_ids=["copernicus_dem_glo30", f"scenario_{scenario_id}"],
        processing_method=f"{connectivity_mode}_hydrologic_connectivity_labeling",
        formula="flood_cells = connected_components(DEM <= threshold, ocean_seeds)",
        units="flooded_area: m²; depth: meters",
        scenario_id=scenario_id,
        confidence=0.89,
        limitations=[
            "Screening model: Does not resolve wave action or sea walls.",
            "Assumes hydrostatically connected steady-state water elevation.",
        ],
    )


def _summarize_parcel_flood(
    conn_flood: np.ndarray,
    unconnected: np.ndarray,
    depth_grid: np.ndarray,
    parcel_cells: np.ndarray,
    pixel_area_sqm: float,
) -> ParcelFloodSummary:
    """Summarize cell counts, depths, and spatial extents inside parcel boundary."""
    total_cells = int(np.sum(parcel_cells))
    total_area = total_cells * pixel_area_sqm if total_cells > 0 else pixel_area_sqm

    flooded_cells = conn_flood & parcel_cells
    f_count = int(np.sum(flooded_cells))
    u_count = int(np.sum(unconnected & parcel_cells))

    f_area = f_count * pixel_area_sqm
    fraction = f_area / max(1.0, total_area)
    depth_stats = _compute_depth_statistics(depth_grid, flooded_cells, f_count)

    return ParcelFloodSummary(
        total_area_sqm=total_area,
        flooded_area_sqm=f_area,
        flooded_percent=fraction * 100.0,
        flooded_fraction=fraction,
        unconnected_count=u_count,
        depth_stats=depth_stats,
    )


class ConnectedInundationEngine:
    """Computes hydrologically connected coastal and inland inundation extents."""

    def __init__(
        self,
        connectivity_mode: Literal["4_way", "8_way"] = "8_way",
    ) -> None:
        """Initialize connectivity structure (4-way cross or 8-way Moore neighborhood)."""
        rank = 2
        connectivity = 1 if connectivity_mode == "4_way" else 2
        self.struct = generate_binary_structure(rank, connectivity)
        self.connectivity_mode = connectivity_mode

    def compute_connected_flood(
        self,
        elevation_grid: np.ndarray,
        water_threshold_m: float,
        ocean_seed_mask: np.ndarray,
        subsidence_grid_m: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute hydrologically connected flood extent.

        Args:
            elevation_grid: 2D array of baseline ground elevations.
            water_threshold_m: Future water surface elevation above datum.
            ocean_seed_mask: Boolean 2D mask of valid open ocean / estuary cells.
            subsidence_grid_m: Optional vertical displacement (positive = subsidence).
        """
        if subsidence_grid_m is not None:
            effective_elevation = elevation_grid - subsidence_grid_m
        else:
            effective_elevation = elevation_grid

        submerged = (effective_elevation <= water_threshold_m) & ~np.isnan(
            effective_elevation
        )

        if not np.any(submerged) or not np.any(ocean_seed_mask):
            dry_shape = elevation_grid.shape
            return (
                np.zeros(dry_shape, dtype=bool),
                np.zeros(dry_shape, dtype=bool),
                np.zeros(dry_shape, dtype=np.float32),
            )

        labeled_array, _ = label(submerged, structure=self.struct)
        seed_labels = np.unique(labeled_array[ocean_seed_mask & submerged])
        seed_labels = seed_labels[seed_labels > 0]

        connected_flood = np.isin(labeled_array, seed_labels)
        unconnected_pockets = submerged & ~connected_flood

        depth_grid = np.zeros_like(elevation_grid, dtype=np.float32)
        depth_grid[connected_flood] = np.maximum(
            0.0, water_threshold_m - effective_elevation[connected_flood]
        )

        return connected_flood, unconnected_pockets, depth_grid

    def evaluate_parcel_scenario(
        self,
        elevation_grid: np.ndarray,
        parcel_mask: np.ndarray,
        ocean_seed_mask: np.ndarray,
        params: ScenarioParameters,
    ) -> tuple[InundationScenarioResult, np.ndarray, np.ndarray]:
        """Evaluate a specific SLR scenario for a parcel using ScenarioParameters."""
        conn_flood, unconnected, depth_grid = self.compute_connected_flood(
            elevation_grid=elevation_grid,
            water_threshold_m=params.water_level_rise_m,
            ocean_seed_mask=ocean_seed_mask,
            subsidence_grid_m=params.subsidence_grid_m,
        )

        parcel_cells = parcel_mask & ~np.isnan(elevation_grid)
        summary = _summarize_parcel_flood(
            conn_flood, unconnected, depth_grid, parcel_cells, params.pixel_area_sqm
        )
        lineage = _build_inundation_lineage(params.scenario_id, self.connectivity_mode)

        result = InundationScenarioResult(
            scenario_id=params.scenario_id,
            water_level_rise_m=params.water_level_rise_m,
            total_parcel_area_sqm=round(summary.total_area_sqm, 2),
            flooded_area_sqm=round(summary.flooded_area_sqm, 2),
            flooded_percent=round(summary.flooded_percent, 2),
            usable_land_loss_sqm=round(summary.flooded_area_sqm, 2),
            connected_inundation_fraction=round(summary.flooded_fraction, 4),
            flood_depth_mean_m=round(summary.depth_stats.depth_mean, 2),
            flood_depth_p90_m=round(summary.depth_stats.depth_p90, 2),
            max_flood_depth_m=round(summary.depth_stats.depth_max, 2),
            unconnected_low_pocket_count=summary.unconnected_count,
            lineage=lineage,
        )

        return result, conn_flood, depth_grid
