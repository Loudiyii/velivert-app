"""Pydantic schemas for Route entities."""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field
from uuid import UUID


class Waypoint(BaseModel):
    """Single waypoint in a route."""

    intervention_id: UUID
    order: int = Field(..., ge=0)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    estimated_arrival: Optional[datetime] = None
    completed: bool = False


class RouteBase(BaseModel):
    """Base route schema."""

    technician_id: UUID
    date: date
    waypoints: List[Waypoint] = Field(..., min_length=1)


class RouteCreate(RouteBase):
    """Schema for creating a new route."""

    optimization_algorithm: Optional[str] = "OR-Tools VRP"


class RouteUpdate(BaseModel):
    """Schema for updating a route."""

    status: Optional[str] = Field(None, pattern="^(draft|active|completed|cancelled)$")
    waypoints: Optional[List[Waypoint]] = None


class RouteResponse(RouteBase):
    """Schema for route response."""

    id: UUID
    total_distance_meters: Optional[int] = None
    estimated_duration_minutes: Optional[int] = None
    status: str
    optimization_algorithm: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RouteOptimizationRequest(BaseModel):
    """Request schema for route optimization."""

    technician_id: UUID
    date: date
    intervention_ids: List[UUID] = Field(..., min_length=1)
    start_location: Optional[Dict[str, float]] = Field(
        None,
        description="Starting location {'lat': 45.44, 'lon': 4.39}"
    )
    max_working_hours: int = Field(8, ge=1, le=12)
    prioritize_urgent: bool = True


class OptimizedRouteWaypoint(BaseModel):
    """Point d'arrêt dans le trajet optimisé (format simplifié)."""
    intervention_id: str
    order: int
    lat: float
    lon: float
    priority: str
    estimated_arrival: Optional[str] = None
    bike_id: Optional[str] = None
    station_id: Optional[str] = None


class OptimizedRouteResponse(BaseModel):
    """Réponse contenant le trajet optimisé."""
    waypoints: List[OptimizedRouteWaypoint]
    total_distance_meters: int
    estimated_duration_minutes: int
    total_bikes: int
    optimization_algorithm: str
    route_type: str