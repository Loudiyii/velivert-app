"""Pydantic schemas for validation and serialization."""

from app.schemas.gbfs import (
    StationInformationFeed,
    StationStatusFeed,
    FreeBikeStatusFeed,
    SystemInformationFeed,
)
from app.schemas.station import (
    StationBase,
    StationCreate,
    StationUpdate,
    StationResponse,
    StationStatusResponse,
)
from app.schemas.bike import BikeBase, BikeResponse
from app.schemas.intervention import (
    InterventionBase,
    InterventionCreate,
    InterventionUpdate,
    InterventionResponse,
)
from app.schemas.route import RouteBase, RouteCreate, RouteResponse

__all__ = [
    # GBFS
    "StationInformationFeed",
    "StationStatusFeed",
    "FreeBikeStatusFeed",
    "SystemInformationFeed",
    # Stations
    "StationBase",
    "StationCreate",
    "StationUpdate",
    "StationResponse",
    "StationStatusResponse",
    # Bikes
    "BikeBase",
    "BikeResponse",
    # Interventions
    "InterventionBase",
    "InterventionCreate",
    "InterventionUpdate",
    "InterventionResponse",
    # Routes
    "RouteBase",
    "RouteCreate",
    "RouteResponse",
]