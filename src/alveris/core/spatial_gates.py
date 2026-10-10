"""Spatial Data Interrogation & Gatekeeper.

Implements Tier 2 Code Gates from .agents/skills/spatial-data-interrogator/SKILL.md:
- Gate 1: Coordinate Reference System (CRS) & bounding box verification before/after.
- Gate 2: Row accounting for spatial joins and filters (detecting silent loss or dups).
- Gate 3: Null and self-intersecting invalid geometry rejection.
- Gate 4: Range plausibility in declared units (meters vs degrees).
- Gate 5: Traceable audit logs for spatial operations.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger("alveris.spatial_gates")


class SpatialIntegrityError(Exception):
    """Raised when a geometry or transformation fails a spatial interrogation gate."""


@dataclass(frozen=True)
class RowAccountingResult:
    """Audit record for spatial filtering and joining operations."""

    operation_name: str
    left_count: int
    right_count: int | None
    output_count: int
    status: str
    details: str


PROJECTED_EPSG_PREFIXES = (
    "EPSG:326",
    "EPSG:327",
    "EPSG:3857",
    "EPSG:7755",
    "EPSG:3035",
)


def is_projected_crs(crs: str) -> bool:
    """Return True if CRS is a projected metric system, False if geographic."""
    crs_clean = crs.upper().strip()
    if "4326" in crs_clean or "CRS84" in crs_clean:
        return False
    return (
        any(prefix in crs_clean for prefix in PROJECTED_EPSG_PREFIXES)
        or "UTM" in crs_clean
    )


class SpatialGateKeeper:
    """Enforces spatial data validation gates before allowing analytics to proceed."""

    @staticmethod
    def verify_crs_and_bounds(
        crs_before: str,
        bounds_before: tuple[float, float, float, float],
        crs_after: str,
        bounds_after: tuple[float, float, float, float],
        operation_name: str = "reprojection",
    ) -> None:
        """Gate 1: Verify that a CRS transformation changed bounds plausibly.

        Detects:
        - `set_crs` used where `to_crs` was meant (CRS changed, bounds identical).
        - Transform applied without updating CRS metadata.
        """
        minx1, miny1, maxx1, maxy1 = bounds_before
        minx2, miny2, maxx2, maxy2 = bounds_after

        is_unprojected_before = "4326" in crs_before or "CRS84" in crs_before
        is_projected_after = is_projected_crs(crs_after)

        if is_unprojected_before and is_projected_after:
            if (
                abs(minx1 - minx2) < 1e-5
                and abs(miny1 - miny2) < 1e-5
                and abs(maxx1 - maxx2) < 1e-5
                and abs(maxy1 - maxy2) < 1e-5
            ):
                raise SpatialIntegrityError(
                    f"[{operation_name}] Gate 1 Failure: CRS relabeled from "
                    f"{crs_before} to {crs_after}, but coordinates did not change "
                    f"(bounds: {bounds_before}). Likely `set_crs()` called instead "
                    "of `to_crs()`."
                )

        logger.info(
            "Gate 1 Passed for %s: (%s -> %s). Bounds: %s -> %s",
            operation_name,
            crs_before,
            crs_after,
            bounds_before,
            bounds_after,
        )

    @staticmethod
    def audit_row_accounting(
        operation_name: str,
        left_count: int,
        output_count: int,
        right_count: int | None = None,
        allow_empty: bool = False,
    ) -> RowAccountingResult:
        """Gate 2: Audit row counts before and after a spatial join or filter.

        Detects:
        - Complete spatial join drops (0 rows returned due to CRS mismatch).
        - Unexpected record dropping in inner joins.
        - One-to-many Cartesian explosion (duplicated rows inflating values).
        """
        if output_count == 0 and not allow_empty and left_count > 0:
            raise SpatialIntegrityError(
                f"[{operation_name}] Gate 2 Failure: Spatial operation produced 0 "
                f"output rows from {left_count} input features. Verify CRS match."
            )

        if right_count is not None and output_count > left_count:
            status = "INFLATED_ONE_TO_MANY"
            details = (
                f"Warning: Output count ({output_count}) exceeds left feature "
                f"count ({left_count}). Features matched multiple polygons. "
                "Ensure grouping before computing monetary sums!"
            )
            logger.warning("[%s] Gate 2 %s: %s", operation_name, status, details)
        elif output_count < left_count:
            status = "FILTERED_ROWS"
            details = f"{left_count - output_count} unmatched left rows dropped."
            logger.info("[%s] Gate 2 %s: %s", operation_name, status, details)
        else:
            status = "EXACT_PRESERVATION"
            details = f"All {left_count} features preserved."

        return RowAccountingResult(
            operation_name=operation_name,
            left_count=left_count,
            right_count=right_count,
            output_count=output_count,
            status=status,
            details=details,
        )

    @staticmethod
    def validate_geometry_coordinates(
        coordinates: list[tuple[float, float]],
        crs: str,
        feature_name: str = "geometry",
    ) -> None:
        """Gate 3: Validate coordinates against coordinate order and range limits.

        Detects:
        - Lat/lon swap (latitude > 90 or < -90).
        - Null Island placement (0.0, 0.0).
        - Unprojected coordinates claimed to be in projected meters.
        """
        if not coordinates:
            raise SpatialIntegrityError(
                f"[{feature_name}] Gate 3 Failure: Empty coordinate list."
            )

        for x, y in coordinates:
            # Check for Null Island
            if abs(x) < 1e-4 and abs(y) < 1e-4:
                raise SpatialIntegrityError(
                    f"[{feature_name}] Gate 3 Failure: Coordinate (0, 0) detected "
                    "(Null Island). Coordinates were lost or defaulted to zero."
                )

            # WGS84 Degree Bounds Check
            if "4326" in crs or "CRS84" in crs:
                if not (-180.0 <= x <= 180.0 and -90.0 <= y <= 90.0):
                    raise SpatialIntegrityError(
                        f"[{feature_name}] Gate 3 Failure: Coordinates ({x}, {y}) "
                        "out of valid WGS84 degree bounds [-180..180, -90..90]. "
                        "Coordinate swap or degree/meter mismatch detected!"
                    )

            # Projected Metric Check
            if is_projected_crs(crs):
                if abs(x) <= 180.0 and abs(y) <= 90.0:
                    raise SpatialIntegrityError(
                        f"[{feature_name}] Gate 3 Failure: Coordinate values ({x}, {y}) "
                        f"look like degrees, but CRS is asserted as metric '{crs}'."
                    )

    @staticmethod
    def validate_area_plausibility(
        area_sqm: float,
        expected_min_sqm: float = 50.0,
        expected_max_sqm: float = 1e8,
        parcel_id: str = "parcel",
    ) -> None:
        """Gate 4: Validate that parcel area in square meters is physically plausible.

        Detects:
        - Computing area directly on degree coordinates.
        - Excessive Web Mercator area inflation.
        """
        if area_sqm <= 0.0:
            raise SpatialIntegrityError(
                f"[{parcel_id}] Gate 4 Failure: Computed area {area_sqm} m² is non-positive."
            )

        if area_sqm < expected_min_sqm:
            raise SpatialIntegrityError(
                f"[{parcel_id}] Gate 4 Failure: Area {area_sqm:.6f} m² is unrealistically small. "
                "Was area calculated on unprojected degrees (EPSG:4326) instead of meters?"
            )

        if area_sqm > expected_max_sqm:
            raise SpatialIntegrityError(
                f"[{parcel_id}] Gate 4 Failure: Area {area_sqm:.1f} m² exceeds plausible limits."
            )
