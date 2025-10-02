"""Optimized route database models."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, TIMESTAMP, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.database import Base


class OptimizedRoute(Base):
    """Optimized maintenance routes for technicians."""

    __tablename__ = "optimized_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    technician_id = Column(UUID(as_uuid=True), nullable=False)
    date = Column(Date, nullable=False)
    route_geometry = Column(Text, nullable=True)  # GeoJSON or WKT string
    waypoints = Column(JSONB, nullable=True)  # Array of intervention waypoints with order
    total_distance_meters = Column(Integer, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)  # draft, active, completed, cancelled
    optimization_algorithm = Column(String(50), nullable=True)  # e.g., "OR-Tools VRP"
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_routes_technician_date', 'technician_id', 'date'),
        Index('idx_routes_status', 'status'),
    )

    def __repr__(self):
        return f"<OptimizedRoute(id='{self.id}', technician='{self.technician_id}', date='{self.date}')>"