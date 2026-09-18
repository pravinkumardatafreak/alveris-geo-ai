"""Ingestion module for ALVERIS: Handles parcel geometries, terrain, and satellite data."""

from alveris.ingestion.cadastre import (
    AgriculturalCultivationResult,
    CadastralAdjudicationResult,
    InformalSettlementEncroachmentResult,
    adjudicate_agricultural_cultivation,
    adjudicate_cadastral_boundaries,
    detect_informal_settlement_encroachment,
)
from alveris.ingestion.parcel import ParcelAsset, load_parcel_from_geojson

__all__ = [
    "AgriculturalCultivationResult",
    "CadastralAdjudicationResult",
    "InformalSettlementEncroachmentResult",
    "ParcelAsset",
    "adjudicate_agricultural_cultivation",
    "adjudicate_cadastral_boundaries",
    "detect_informal_settlement_encroachment",
    "load_parcel_from_geojson",
]

