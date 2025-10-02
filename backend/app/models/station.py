"""Station related database models."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, TIMESTAMP, Text, ARRAY, ForeignKey, Index
from app.database import Base


class Station(Base):
    """Static information about bike stations."""

    __tablename__ = "stations"

    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    lat = Column(DECIMAL(10, 8), nullable=False)
    lon = Column(DECIMAL(11, 8), nullable=False)
    address = Column(Text, nullable=True)
    capacity = Column(Integer, nullable=False)
    region_id = Column(String(50), nullable=True)
    rental_methods = Column(ARRAY(Text), nullable=True)
    is_virtual_station = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Station(id='{self.id}', name='{self.name}')>"


class StationStatusSnapshot(Base):
    """
    Time-series snapshots of station status.
    This table will be converted to a TimescaleDB hypertable.
    """

    __tablename__ = "station_status_snapshots"

    time = Column(TIMESTAMP(timezone=True), nullable=False, primary_key=True)
    station_id = Column(
        String(50),
        ForeignKey('stations.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True
    )
    num_bikes_available = Column(Integer, nullable=False)
    num_bikes_disabled = Column(Integer, default=0)
    num_docks_available = Column(Integer, nullable=False)
    num_docks_disabled = Column(Integer, default=0)
    is_installed = Column(Boolean, default=True)
    is_renting = Column(Boolean, default=True)
    is_returning = Column(Boolean, default=True)
    last_reported = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_station_snapshots_time', 'station_id', 'time'),
    )

    def __repr__(self):
        return f"<StationStatusSnapshot(station_id='{self.station_id}', time='{self.time}')>"