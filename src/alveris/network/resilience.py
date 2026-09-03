"""Road network resilience and emergency evacuation detour engine.

Implements Phase 7 of ALVERIS:
- Graph-based road network modeling (nodes, edges, lengths, and classifications).
- Raster flood depth overlay and vehicular passability thresholding:
    Passable if max_flood_depth < passability_threshold_m (e.g. 0.30m for emergency/suv).
- Shortest path routing under baseline vs. flooded network states using Dijkstra's algorithm.
- Detour ratio computation:
    DetourRatio = Distance_flooded / Distance_baseline
- Physical isolation / severance detection (infinite detour ratio / islanding).
- Composite network accessibility scoring (0.0 to 100.0) for collateral risk haircuts.
- Data lineage generation per Section 6 of the Master Specification.
"""

from dataclasses import dataclass
from typing import Any

import networkx as nx
import numpy as np
from pydantic import BaseModel, Field

from alveris.core.lineage import DerivedFeatureLineage


class NetworkResilienceMetrics(BaseModel):
    """Parcel accessibility and emergency routing metrics under flood stress."""

    scenario_id: str = Field(..., description="Evaluated scenario identifier.")
    baseline_route_distance_m: float = Field(
        ..., gt=0.0, description="Shortest path distance to arterial road under dry baseline (m)."
    )
    flooded_route_distance_m: float | None = Field(
        default=None,
        description="Shortest path distance through passable network under flood stress (m).",
    )
    detour_ratio: float = Field(
        ...,
        ge=1.0,
        description="Ratio of flooded route distance to baseline route distance (>= 1.0).",
    )
    is_physically_isolated: bool = Field(
        ..., description="True if no passable path connects the parcel to the arterial network."
    )
    impassable_edge_count: int = Field(
        ..., ge=0, description="Number of submerged road links exceeding passability depth."
    )
    total_network_edges: int = Field(
        ..., gt=0, description="Total road links in the local evaluation graph."
    )
    network_accessibility_score: float = Field(
        ..., ge=0.0, le=100.0, description="0 (completely severed) to 100 (uninhibited access)."
    )
    lineage: DerivedFeatureLineage = Field(
        ..., description="Provenance metadata tracing OpenStreetMap / OSMnx graph."
    )


@dataclass(frozen=True)
class NetworkEvaluationConfig:
    """Configuration for road passability and isolation thresholds."""

    passability_depth_threshold_m: float = 0.30  # Standard emergency/SUV passability limit
    max_penalty_detour_ratio: float = 10.0  # Cap ratio for finite scoring when severed


def _build_network_lineage(scenario_id: str) -> DerivedFeatureLineage:
    """Build provenance record for road network resilience analysis."""
    return DerivedFeatureLineage(
        feature_name=f"road_network_resilience_{scenario_id}",
        source_dataset_ids=["openstreetmap_road_network", f"scenario_{scenario_id}"],
        processing_method="dijkstra_shortest_path_with_flood_depth_edge_pruning",
        formula="DetourRatio = Distance(flooded_graph) / Distance(baseline_graph)",
        units="distances: meters; detour_ratio: dimensionless; score: [0.0, 100.0]",
        scenario_id=scenario_id,
        confidence=0.90,
        limitations=[
            "Assumes static road crown elevations; does not model culvert hydraulic capacity.",
            "Passability threshold assumes standard high-clearance emergency transit vehicles.",
        ],
    )


def _compute_accessibility_score(
    is_isolated: bool, detour_ratio: float, config: NetworkEvaluationConfig
) -> float:
    """Compute institutional network accessibility score from 0.0 to 100.0."""
    if is_isolated:
        return 0.0

    ratio_clamped = min(detour_ratio, config.max_penalty_detour_ratio)
    score = (
        (config.max_penalty_detour_ratio - ratio_clamped)
        / (config.max_penalty_detour_ratio - 1.0)
        * 100.0
    )
    return round(float(np.clip(score, 0.0, 100.0)), 1)


def _solve_flooded_route(
    passable_g: nx.Graph,
    origin: Any,
    destination: Any,
    baseline_dist: float,
    max_penalty_ratio: float,
) -> tuple[float | None, bool, float]:
    """Calculate shortest passable path under flood disruption."""
    try:
        dist = float(
            nx.shortest_path_length(
                passable_g, source=origin, target=destination, weight="weight"
            )
        )
        return round(dist, 1), False, round(dist / max(1.0, baseline_dist), 2)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None, True, max_penalty_ratio


class RoadNetworkResilienceEngine:
    """Evaluates access road inundation, route severing, and evacuation detour penalties."""

    def __init__(self, config: NetworkEvaluationConfig | None = None) -> None:
        """Initialize engine with configurable depth thresholds."""
        self.config = config or NetworkEvaluationConfig()

    def filter_passable_graph(
        self,
        graph: nx.MultiGraph | nx.Graph,
        edge_flood_depths: dict[tuple[Any, Any], float],
    ) -> tuple[nx.Graph, int]:
        """Prune road edges that exceed vehicular water depth passability threshold."""
        passable_g = nx.Graph()

        for node, data in graph.nodes(data=True):
            passable_g.add_node(node, **data)

        impassable_count = 0
        thresh = self.config.passability_depth_threshold_m

        for u, v, data in graph.edges(data=True):
            depth = edge_flood_depths.get((u, v), edge_flood_depths.get((v, u), 0.0))
            if depth < thresh:
                weight = data.get("length", 1.0)
                passable_g.add_edge(u, v, weight=weight, flood_depth=depth, **data)
            else:
                impassable_count += 1

        return passable_g, impassable_count

    def evaluate_route_resilience(
        self,
        base_graph: nx.Graph,
        origin_node: Any,
        destination_node: Any,
        edge_flood_depths: dict[tuple[Any, Any], float],
        scenario_id: str = "slr_1_0",
    ) -> NetworkResilienceMetrics:
        """Compute baseline route, flooded detour route, and accessibility impact metrics."""
        try:
            baseline_dist = float(
                nx.shortest_path_length(
                    base_graph, source=origin_node, target=destination_node, weight="length"
                )
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound) as err:
            raise ValueError(f"Origin or destination node unreachable in baseline: {err}") from err

        passable_g, impassable_count = self.filter_passable_graph(
            base_graph, edge_flood_depths
        )

        flooded_dist, is_isolated, detour_ratio = _solve_flooded_route(
            passable_g,
            origin_node,
            destination_node,
            baseline_dist,
            self.config.max_penalty_detour_ratio,
        )

        access_score = _compute_accessibility_score(
            is_isolated, detour_ratio, self.config
        )
        lineage = _build_network_lineage(scenario_id)

        return NetworkResilienceMetrics(
            scenario_id=scenario_id,
            baseline_route_distance_m=round(baseline_dist, 1),
            flooded_route_distance_m=flooded_dist,
            detour_ratio=detour_ratio,
            is_physically_isolated=is_isolated,
            impassable_edge_count=impassable_count,
            total_network_edges=base_graph.number_of_edges(),
            network_accessibility_score=access_score,
            lineage=lineage,
        )
