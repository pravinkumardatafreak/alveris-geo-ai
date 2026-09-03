"""Ingestion module for ALVERIS: Handles parcel geometries, terrain, and satellite data."""

from alveris.ingestion.parcel import ParcelAsset, load_parcel_from_geojson

__all__ = ["ParcelAsset", "load_parcel_from_geojson"]
