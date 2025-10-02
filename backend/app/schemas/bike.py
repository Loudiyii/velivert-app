"""Pydantic schemas for Bike entities."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal


class BikeBase(BaseModel):
    """Base bike schema."""

    bike_id: str = Field(..., min_length=1, max_length=50)
    vehicle_type_id: Optional[str] = None
    current_station_id: Optional[str] = None
    lat: Optional[Decimal] = Field(None, ge=-90, le=90)
    lon: Optional[Decimal] = Field(None, ge=-180, le=180)
    is_reserved: bool = False
    is_disabled: bool = False
    current_range_meters: Optional[int] = Field(None, ge=0)


class BikeResponse(BikeBase):
    """Schema for bike response."""

    last_reported: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BikeStatusUpdate(BaseModel):
    """Schema for updating bike status from GBFS."""

    lat: Decimal = Field(..., ge=-90, le=90)
    lon: Decimal = Field(..., ge=-180, le=180)
    is_reserved: bool = False
    is_disabled: bool = False
    vehicle_type_id: Optional[str] = None
    current_range_meters: Optional[int] = Field(None, ge=0)
    station_id: Optional[str] = None