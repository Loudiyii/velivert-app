"""Pydantic schemas for Maintenance Intervention entities."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID
from decimal import Decimal


class InterventionBase(BaseModel):
    """Base intervention schema."""

    bike_id: Optional[str] = Field(None, min_length=1, max_length=50)
    station_id: Optional[str] = Field(None, min_length=1, max_length=50)
    intervention_type: str = Field(..., min_length=1, max_length=50)
    priority: str = Field(..., pattern="^(low|medium|high|urgent)$")
    description: Optional[str] = Field(None, max_length=1000)
    scheduled_at: Optional[datetime] = None

    @field_validator('bike_id', 'station_id')
    @classmethod
    def validate_target(cls, v, info):
        """Ensure at least one target is specified."""
        # This will be checked in model_validator
        return v


class InterventionCreate(InterventionBase):
    """Schema for creating a new intervention."""

    technician_id: Optional[UUID] = None

    @model_validator(mode='after')
    def validate_bike_or_station(self):
        """Ensure bike_id or station_id is provided."""
        if not self.bike_id and not self.station_id:
            raise ValueError("Either bike_id or station_id must be provided")
        return self


class InterventionUpdate(BaseModel):
    """Schema for updating an intervention."""

    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=2000)


class InterventionResponse(InterventionBase):
    """Schema for intervention response."""

    id: UUID
    technician_id: Optional[UUID] = None
    status: str
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterventionListQuery(BaseModel):
    """Query parameters for listing interventions."""

    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    technician_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None