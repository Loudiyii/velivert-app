"""Pydantic schemas for Station entities."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal


class StationBase(BaseModel):
    """Base station schema."""

    name: str = Field(..., min_length=1, max_length=255)
    lat: Decimal = Field(..., ge=-90, le=90)
    lon: Decimal = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    capacity: int = Field(..., ge=0)
    region_id: Optional[str] = None
    rental_methods: Optional[List[str]] = None
    is_virtual_station: bool = False


class StationCreate(StationBase):
    """Schema for creating a new station."""

    id: str = Field(..., min_length=1, max_length=50)


class StationUpdate(BaseModel):
    """Schema for updating a station."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)
    is_virtual_station: Optional[bool] = None


class StationResponse(StationBase):
    """Schema for station response."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StationStatusResponse(BaseModel):
    """Schema for station status response."""

    station_id: str
    name: str
    lat: float
    lon: float
    capacity: int
    num_bikes_available: int
    num_bikes_disabled: int
    num_docks_available: int
    num_docks_disabled: int
    is_installed: bool
    is_renting: bool
    is_returning: bool
    last_reported: datetime
    occupancy_rate: Optional[float] = Field(None, ge=0, le=1, description="Bikes available / capacity")

    class Config:
        from_attributes = True


class StationHistoryQuery(BaseModel):
    """Query parameters for station history."""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    interval: Optional[str] = Field("1 hour", description="Time bucket interval (e.g., '1 hour', '15 minutes')")


class StationHistoryPoint(BaseModel):
    """Single point in station history."""

    time: datetime
    avg_bikes_available: float
    min_bikes_available: int
    max_bikes_available: int

    class Config:
        from_attributes = True