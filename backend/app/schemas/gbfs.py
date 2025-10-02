"""Pydantic schemas for GBFS API validation (GBFS v2.2 spec)."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class GBFSBase(BaseModel):
    """Base GBFS response structure."""

    last_updated: int = Field(..., description="POSIX timestamp")
    ttl: int = Field(..., description="Time to live in seconds")
    version: str = Field(..., description="GBFS version")

    @field_validator('last_updated')
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp is reasonable."""
        if v < 0:
            raise ValueError("Timestamp cannot be negative")
        return v


# ==================== Station Information ====================

class StationInfo(BaseModel):
    """Individual station static information."""

    station_id: str
    name: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    capacity: int = Field(..., ge=0)
    region_id: Optional[str] = None
    rental_methods: Optional[List[str]] = None
    is_virtual_station: Optional[bool] = False


class StationInformationData(BaseModel):
    """Station information data container."""

    stations: List[StationInfo]


class StationInformationFeed(GBFSBase):
    """Complete station_information.json feed."""

    data: StationInformationData


# ==================== Station Status ====================

class StationStatus(BaseModel):
    """Individual station real-time status."""

    station_id: str
    num_bikes_available: int = Field(..., ge=0)
    num_bikes_disabled: Optional[int] = Field(0, ge=0)
    num_docks_available: int = Field(..., ge=0)
    num_docks_disabled: Optional[int] = Field(0, ge=0)
    is_installed: bool = True
    is_renting: bool = True
    is_returning: bool = True
    last_reported: int

    @field_validator('last_reported')
    @classmethod
    def validate_last_reported(cls, v):
        """Validate timestamp is reasonable."""
        if v < 0:
            raise ValueError("Timestamp cannot be negative")
        return v


class StationStatusData(BaseModel):
    """Station status data container."""

    stations: List[StationStatus]


class StationStatusFeed(GBFSBase):
    """Complete station_status.json feed."""

    data: StationStatusData


# ==================== Free Bike Status ====================

class FreeBike(BaseModel):
    """Individual free-floating bike status."""

    bike_id: str
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    is_reserved: bool = False
    is_disabled: bool = False
    vehicle_type_id: Optional[str] = None
    current_range_meters: Optional[int] = Field(None, ge=0)
    station_id: Optional[str] = None


class FreeBikeStatusData(BaseModel):
    """Free bike status data container."""

    bikes: List[FreeBike]


class FreeBikeStatusFeed(GBFSBase):
    """Complete free_bike_status.json feed."""

    data: FreeBikeStatusData


# ==================== System Information ====================

class SystemInformationData(BaseModel):
    """System information data."""

    system_id: str
    language: str
    name: str
    timezone: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    operator: Optional[str] = None
    url: Optional[str] = None


class SystemInformationFeed(GBFSBase):
    """Complete system_information.json feed."""

    data: SystemInformationData


# ==================== Vehicle Types ====================

class VehicleType(BaseModel):
    """Vehicle type definition."""

    vehicle_type_id: str
    form_factor: str  # bicycle, scooter, etc.
    propulsion_type: str  # human, electric_assist, electric
    max_range_meters: Optional[int] = None
    name: Optional[str] = None


class VehicleTypesData(BaseModel):
    """Vehicle types data container."""

    vehicle_types: List[VehicleType]


class VehicleTypesFeed(GBFSBase):
    """Complete vehicle_types.json feed."""

    data: VehicleTypesData