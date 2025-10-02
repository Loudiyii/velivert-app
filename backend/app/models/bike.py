"""Bike related database models."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, TIMESTAMP, ForeignKey, Index
from app.database import Base


class Bike(Base):
    """Information about individual bikes (including free-floating bikes)."""

    __tablename__ = "bikes"

    bike_id = Column(String(50), primary_key=True)
    vehicle_type_id = Column(String(50), nullable=True)
    current_station_id = Column(
        String(50),
        ForeignKey('stations.id', ondelete='SET NULL'),
        nullable=True
    )
    lat = Column(DECIMAL(10, 8), nullable=True)
    lon = Column(DECIMAL(11, 8), nullable=True)
    is_reserved = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    current_range_meters = Column(Integer, nullable=True)
    last_reported = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_bikes_station', 'current_station_id'),
        Index('idx_bikes_disabled', 'is_disabled'),
    )

    def __repr__(self):
        return f"<Bike(bike_id='{self.bike_id}', station='{self.current_station_id}')>"