"""Unit tests for ALVERIS Spatial GateKeeper (Tier 2 Code Gates)."""

import pytest

from alveris.core.spatial_gates import SpatialGateKeeper, SpatialIntegrityError


def test_gate1_catches_set_crs_misuse():
    """Gate 1 must raise an error if CRS was relabeled to projected UTM but bounds stayed in degrees."""
    degree_bounds = (80.3125, 13.2450, 80.3155, 13.2480)

    with pytest.raises(SpatialIntegrityError, match="set_crs"):
        SpatialGateKeeper.verify_crs_and_bounds(
            crs_before="EPSG:4326",
            bounds_before=degree_bounds,
            crs_after="EPSG:32644",
            bounds_after=degree_bounds,  # Identical coordinates: set_crs mistake!
        )


def test_gate1_passes_legitimate_reprojection():
    """Gate 1 passes when coordinates expand to metric planar ranges upon reprojection."""
    degree_bounds = (80.3125, 13.2450, 80.3155, 13.2480)
    utm_bounds = (425400.0, 1464300.0, 425725.0, 1464630.0)

    # Should execute without error
    SpatialGateKeeper.verify_crs_and_bounds(
        crs_before="EPSG:4326",
        bounds_before=degree_bounds,
        crs_after="EPSG:32644",
        bounds_after=utm_bounds,
    )


def test_gate2_catches_zero_row_spatial_join():
    """Gate 2 must catch silent complete loss in spatial join or filtering."""
    with pytest.raises(SpatialIntegrityError, match="produced 0 output rows"):
        SpatialGateKeeper.audit_row_accounting(
            operation_name="parcel_flood_overlay",
            left_count=15,
            output_count=0,
            right_count=1,
            allow_empty=False,
        )


def test_gate3_catches_null_island_and_coordinate_swaps():
    """Gate 3 must detect (0,0) Null Island and latitude > 90 degree coordinate swaps."""
    with pytest.raises(SpatialIntegrityError, match="Null Island"):
        SpatialGateKeeper.validate_geometry_coordinates(
            coordinates=[(0.0, 0.0)],
            crs="EPSG:4326",
        )

    with pytest.raises(SpatialIntegrityError, match="out of valid WGS84 degree bounds"):
        SpatialGateKeeper.validate_geometry_coordinates(
            coordinates=[(80.25, 120.5)],  # Latitude 120.5 exceeds 90!
            crs="EPSG:4326",
        )

    with pytest.raises(SpatialIntegrityError, match="look like degrees"):
        SpatialGateKeeper.validate_geometry_coordinates(
            coordinates=[(80.25, 13.05)],  # Degree coordinates claimed in UTM
            crs="EPSG:32644",
        )


def test_gate4_catches_area_calculated_in_degrees():
    """Gate 4 must flag areas that are absurdly small, characteristic of calculating area in degrees²."""
    with pytest.raises(SpatialIntegrityError, match="unrealistically small"):
        SpatialGateKeeper.validate_area_plausibility(
            area_sqm=0.000008,  # Typical degree² area mistaken for m²
            parcel_id="test_parcel",
        )

    # Plausible parcel area in m² must pass
    SpatialGateKeeper.validate_area_plausibility(
        area_sqm=12500.0,
        parcel_id="test_parcel",
    )
