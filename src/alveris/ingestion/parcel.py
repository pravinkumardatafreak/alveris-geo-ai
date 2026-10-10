"""Parcel vector ingestion and Coordinate Reference System (CRS) governance engine.

Implements Phase 2 of the ALVERIS Architecture:
- Provider-agnostic GeoJSON parcel ingestion.
- Dynamic UTM zone determination based on geographic centroid.
- Conformal/Equal-area planar metric reprojection.
- Strict Tier 2 spatial interrogation gates (Gate 1, Gate 3, Gate 4).
- Metric area computation (m², hectares, acres).
- Traceable data lineage creation per Section 6 of the Master Specification.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
from pydantic import BaseModel, Field
from shapely.geometry import Polygon, mapping

from alveris.core.lineage import DataMode, DatasetLineage
from alveris.core.spatial_gates import SpatialGateKeeper, SpatialIntegrityError


def get_utm_epsg_from_lonlat(lon: float, lat: float) -> str:
    """Derive standard EPSG code for the Universal Transverse Mercator (UTM) zone.

    Formula:
        zone = floor((lon + 180) / 6) + 1
        EPSG:326xx for Northern Hemisphere (lat >= 0)
        EPSG:327xx for Southern Hemisphere (lat < 0)
    """
    if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
        raise SpatialIntegrityError(
            f"Coordinates ({lon}, {lat}) out of valid WGS84 bounds."
        )
    zone = int((lon + 180.0) // 6.0) + 1
    epsg_number = 32600 + zone if lat >= 0.0 else 32700 + zone
    return f"EPSG:{epsg_number}"


@dataclass(frozen=True)
class PlanarMetricResult:
    """Aggregated planar and metric spatial computation results."""

    utm_epsg: str
    bounds_utm: tuple[float, float, float, float]
    centroid_wgs84: tuple[float, float]
    centroid_utm: tuple[float, float]
    area_sqm: float


class ParcelAsset(BaseModel):
    """Standardized, validated parcel asset model with metric planar properties."""

    asset_id: str = Field(..., description="Unique parcel asset identifier.")
    name: str = Field(..., description="Human-readable asset title.")
    land_use_class: str = Field(..., description="Operational land-use class.")
    baseline_market_value_inr: float = Field(
        ...,
        gt=0.0,
        description="Baseline unadjusted market value estimate in INR.",
    )
    source_crs: str = Field(
        default="EPSG:4326",
        description="Horizontal CRS of the source cadastral file.",
    )
    utm_epsg: str = Field(
        ...,
        description="Projected metric UTM CRS used for metric operations.",
    )
    vertical_datum: str = Field(
        default="EGM2008",
        description="Vertical elevation datum reference.",
    )
    bounds_wgs84: tuple[float, float, float, float] = Field(
        ...,
        description="(minx, miny, maxx, maxy) in geographic degrees.",
    )
    bounds_utm: tuple[float, float, float, float] = Field(
        ...,
        description="(minx, miny, maxx, maxy) in metric planar meters.",
    )
    centroid_wgs84: tuple[float, float] = Field(
        ...,
        description="(longitude, latitude) of the asset centroid.",
    )
    centroid_utm: tuple[float, float] = Field(
        ...,
        description="(easting, northing) in metric planar UTM meters.",
    )
    area_sqm: float = Field(..., gt=0.0, description="Area in square meters.")
    area_hectares: float = Field(..., gt=0.0, description="Area in hectares.")
    area_acres: float = Field(..., gt=0.0, description="Area in acres.")
    geometry_geojson: dict[str, Any] = Field(
        ...,
        description="GeoJSON geometry dictionary in WGS84 for web mapping.",
    )
    lineage: DatasetLineage = Field(
        ...,
        description="Data provenance metadata describing cadastral origin.",
    )


def _compute_planar_metrics(
    geom_wgs: Polygon,
    source_crs: str,
    parcel_name: str,
    override_utm_epsg: str | None = None,
) -> PlanarMetricResult:
    """Reproject geometry to metric UTM and compute validated planar measurements."""
    cen_wgs = geom_wgs.centroid
    cen_lon, cen_lat = float(cen_wgs.x), float(cen_wgs.y)
    utm_epsg = override_utm_epsg or get_utm_epsg_from_lonlat(cen_lon, cen_lat)

    gdf_single = gpd.GeoDataFrame(geometry=[geom_wgs], crs=source_crs)
    gdf_utm = gdf_single.to_crs(utm_epsg)
    geom_utm: Polygon = gdf_utm.geometry.iloc[0]

    bounds_utm = geom_utm.bounds
    SpatialGateKeeper.verify_crs_and_bounds(
        crs_before=source_crs,
        bounds_before=geom_wgs.bounds,
        crs_after=utm_epsg,
        bounds_after=bounds_utm,
        operation_name="parcel_to_utm_projection",
    )

    area_sqm = float(geom_utm.area)
    SpatialGateKeeper.validate_area_plausibility(
        area_sqm=area_sqm,
        expected_min_sqm=50.0,
        expected_max_sqm=5e7,
        parcel_id=parcel_name,
    )

    cen_utm = geom_utm.centroid
    return PlanarMetricResult(
        utm_epsg=utm_epsg,
        bounds_utm=bounds_utm,
        centroid_wgs84=(cen_lon, cen_lat),
        centroid_utm=(float(cen_utm.x), float(cen_utm.y)),
        area_sqm=area_sqm,
    )


def _read_and_validate_geojson(
    path: Path,
) -> tuple[dict[str, Any], str, Polygon]:
    """Read GeoJSON file, validate geometry validity and coordinate bounds."""
    if not path.exists():
        raise FileNotFoundError(f"Cadastral parcel file not found: {path}")

    gdf = gpd.read_file(path)
    if gdf.empty:
        raise SpatialIntegrityError(f"GeoJSON file '{path}' contains no features.")

    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    source_crs = f"EPSG:{gdf.crs.to_epsg()}" if gdf.crs.to_epsg() else "EPSG:4326"

    first_row = gdf.iloc[0]
    geom: Polygon = first_row.geometry

    if not geom.is_valid:
        raise SpatialIntegrityError(f"Invalid geometry in '{path.name}'.")

    SpatialGateKeeper.validate_geometry_coordinates(
        coordinates=[(c[0], c[1]) for c in geom.exterior.coords],
        crs=source_crs,
        feature_name=path.stem,
    )

    props = dict(first_row)
    props.pop("geometry", None)
    return props, source_crs, geom


def _build_cadastral_lineage(
    asset_id: str, path: Path, source_crs: str, vertical_datum: str
) -> DatasetLineage:
    """Build provenance record for an ingested cadastral parcel."""
    return DatasetLineage(
        dataset_id=f"cadastral_{asset_id}",
        provider="Local Cadastral Survey / User Boundary",
        source_url=str(path.resolve()),
        acquisition_date="2025-01-01",
        crs=source_crs,
        vertical_datum=vertical_datum,
        resolution="vector_polygon",
        units="planar_metric_meters",
        license="Confidential / Project Fixture",
        data_mode=DataMode.OBSERVED,
    )


def load_parcel_from_geojson(
    file_path: str | Path,
    override_utm_epsg: str | None = None,
    vertical_datum: str = "EGM2008",
) -> ParcelAsset:
    """Load, validate, project, and measure a parcel from a GeoJSON vector file."""
    path = Path(file_path)
    props, source_crs, geom = _read_and_validate_geojson(path)

    metrics = _compute_planar_metrics(
        geom, source_crs, path.stem, override_utm_epsg
    )

    asset_id = str(props.get("asset_id", path.stem))
    name = str(props.get("name", f"Asset {asset_id}"))
    land_use = str(props.get("land_use_class", "unclassified"))
    val = float(props.get("baseline_market_value_inr", 10000000.0))

    lineage = _build_cadastral_lineage(asset_id, path, source_crs, vertical_datum)

    return ParcelAsset(
        asset_id=asset_id,
        name=name,
        land_use_class=land_use,
        baseline_market_value_inr=val,
        source_crs=source_crs,
        utm_epsg=metrics.utm_epsg,
        vertical_datum=vertical_datum,
        bounds_wgs84=geom.bounds,
        bounds_utm=metrics.bounds_utm,
        centroid_wgs84=metrics.centroid_wgs84,
        centroid_utm=metrics.centroid_utm,
        area_sqm=round(metrics.area_sqm, 2),
        area_hectares=round(metrics.area_sqm / 10000.0, 4),
        area_acres=round(metrics.area_sqm / 4046.8564224, 4),
        geometry_geojson=mapping(geom),
        lineage=lineage,
    )
