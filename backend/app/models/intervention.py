"""Maintenance intervention database models."""

from datetime import datetime
from sqlalchemy import Column, String, Text, TIMESTAMP, Index, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base


class MaintenanceIntervention(Base):
    """Maintenance interventions for bikes and stations."""

    __tablename__ = "maintenance_interventions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bike_id = Column(String(50), nullable=True)
    station_id = Column(String(50), nullable=True)
    technician_id = Column(UUID(as_uuid=True), nullable=True)
    intervention_type = Column(String(50), nullable=False)  # repair, relocation, battery_swap, etc.
    priority = Column(String(20), nullable=False)  # low, medium, high, urgent
    status = Column(String(20), nullable=False)  # pending, in_progress, completed, cancelled
    description = Column(Text, nullable=True)
    scheduled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    lat = Column(DECIMAL(10, 8), nullable=True)
    lon = Column(DECIMAL(11, 8), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_interventions_status', 'status'),
        Index('idx_interventions_priority', 'priority'),
        Index('idx_interventions_technician', 'technician_id'),
        Index('idx_interventions_scheduled', 'scheduled_at'),
    )

    def __repr__(self):
        return f"<MaintenanceIntervention(id='{self.id}', type='{self.intervention_type}', status='{self.status}')>"