"""Ingestion module for ALVERIS: Handles parcel geometries, terrain, and satellite data."""

from alveris.ingestion.cadastre import CadastralAdjudicationResult, adjudicate_cadastral_boundaries
from alveris.ingestion.parcel import ParcelAsset, load_parcel_from_geojson

__all__ = [
    "CadastralAdjudicationResult",
    "ParcelAsset",
    "adjudicate_cadastral_boundaries",
    "load_parcel_from_geojson",
]
