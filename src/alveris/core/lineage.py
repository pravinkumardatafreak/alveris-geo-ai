"""Data lineage and governance schemas for ALVERIS.

Implements Section 6, Section 7, and Section 41 of the Master Specification:
- Full traceability back to raw satellite, elevation, or cadastral sources.
- Explicit CRS, vertical datum, and conversion status.
- Strict categorization by DataMode (OBSERVED, DERIVED, SIMULATED, SYNTHETIC).
"""

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DataMode(str, Enum):
    """Classification of data origin to prevent claiming synthetic data as observed."""

    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    SIMULATED = "SIMULATED"
    SYNTHETIC = "SYNTHETIC"


class DatasetLineage(BaseModel):
    """Metadata describing the origin, datum, and resolution of an ingested dataset."""

    dataset_id: str = Field(
        ...,
        description="Unique machine-readable dataset identifier.",
    )
    provider: str = Field(
        ...,
        description="Entity or mission providing data (e.g. ESA, Copernicus, NASA).",
    )
    source_url: str | None = Field(
        default=None,
        description="Direct URL or catalog endpoint.",
    )
    acquisition_date: str = Field(
        ...,
        description="Date or date range of physical sensor observation.",
    )
    release_date: str | None = Field(
        default=None,
        description="Official dataset release or publication date.",
    )
    crs: str = Field(
        ...,
        description="Horizontal CRS (e.g. 'EPSG:4326', 'EPSG:32644').",
    )
    vertical_datum: str = Field(
        ...,
        description="Vertical datum reference (e.g. 'EGM2008', 'Local_MSL').",
    )
    resolution: str = Field(
        ...,
        description="Spatial resolution (e.g. '30m', '10m', '0.5m').",
    )
    units: str = Field(
        ...,
        description="Measurement units (e.g. 'meters', 'mm/year', 'reflectance').",
    )
    nodata: float | int | str | None = Field(
        default=None,
        description="Designated nodata or masked value.",
    )
    license: str = Field(
        default="Open / CC-BY",
        description="Data usage license or copyright.",
    )
    processing_version: str = Field(
        default="v1.0",
        description="Pipeline version that processed the data.",
    )
    ingestion_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of dataset ingestion into ALVERIS.",
    )
    data_mode: DataMode = Field(
        default=DataMode.OBSERVED,
        description="Origin mode: OBSERVED, DERIVED, SIMULATED, or SYNTHETIC.",
    )

    @field_validator("crs")
    @classmethod
    def validate_crs(cls, value: str) -> str:
        """Ensure CRS string is non-empty and follows standard authority formats."""
        clean = value.strip().upper()
        if not clean or not (clean.startswith("EPSG:") or "UTM" in clean):
            raise ValueError(
                f"Invalid CRS format: '{value}'. Specify authority, e.g. 'EPSG:4326'."
            )
        return value.strip()

    @property
    def provenance_hash(self) -> str:
        """Compute deterministic SHA-256 fingerprint for dataset provenance."""
        payload = f"{self.dataset_id}:{self.provider}:{self.crs}:{self.processing_version}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class DerivedFeatureLineage(BaseModel):
    """Metadata tracking mathematical transformation and assumptions for derived metrics."""

    feature_name: str = Field(
        ...,
        description="Canonical metric name (e.g. 'connected_inundation_fraction').",
    )
    source_dataset_ids: list[str] = Field(
        ...,
        description="List of DatasetLineage IDs consumed to produce this feature.",
    )
    processing_method: str = Field(
        ...,
        description="Algorithmic method (e.g. '8-way flood fill', 'NDVI ratio').",
    )
    formula: str | None = Field(
        default=None,
        description="Mathematical equation used in computation.",
    )
    units: str = Field(
        ...,
        description="Output units (e.g. 'fraction 0-1', 'meters', 'INR').",
    )
    time_period: str | None = Field(
        default=None,
        description="Temporal window or baseline period.",
    )
    scenario_id: str | None = Field(
        default=None,
        description="Climate scenario ID if scenario-dependent.",
    )
    model_version: str = Field(
        default="v0.1.0",
        description="ALVERIS model version.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 (unreliable) to 1.0 (high certainty).",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Explicit caveats, assumptions, or unmodeled dynamics.",
    )
    extra_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional technical parameters for reproducibility.",
    )

    @property
    def provenance_hash(self) -> str:
        """Compute deterministic SHA-256 fingerprint for feature provenance."""
        payload = f"{self.feature_name}:{self.processing_method}:{self.model_version}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
