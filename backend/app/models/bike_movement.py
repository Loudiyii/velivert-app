"""Bike movement tracking model."""

from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class BikeMovement(Base):
    """
    Tracks historical movements of bikes between locations.

    This table captures every detected change in bike position,
    allowing us to analyze:
    - Movement patterns between stations
    - Bike usage frequency
    - Popular routes
    - Time-based demand patterns
    """

    __tablename__ = "bike_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bike_id = Column(String, ForeignKey("bikes.bike_id"), nullable=False, index=True)

    # Previous location
    from_station_id = Column(String, ForeignKey("stations.id"), nullable=True)
    from_lat = Column(Float, nullable=True)
    from_lon = Column(Float, nullable=True)

    # New location
    to_station_id = Column(String, ForeignKey("stations.id"), nullable=True)
    to_lat = Column(Float, nullable=False)
    to_lon = Column(Float, nullable=False)

    # Movement metadata
    movement_type = Column(String, nullable=False)  # "pickup", "dropoff", "relocation", "in_transit"
    distance_meters = Column(Float, nullable=True)  # Distance traveled

    # Bike state at time of movement
    is_reserved = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    battery_range_meters = Column(Integer, nullable=True)

    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_bike_movements_bike_detected', 'bike_id', 'detected_at'),
        Index('idx_bike_movements_from_station', 'from_station_id', 'detected_at'),
        Index('idx_bike_movements_to_station', 'to_station_id', 'detected_at'),
        Index('idx_bike_movements_detected_at', 'detected_at'),
        Index('idx_bike_movements_type', 'movement_type', 'detected_at'),
    )

    def __repr__(self):
        return f"<BikeMovement(bike_id={self.bike_id}, type={self.movement_type}, at={self.detected_at})>"


class BikeSnapshot(Base):
    """
    Periodic snapshots of bike state for time-series analysis.

    Lighter than full movement tracking, captures bike state at regular intervals
    for trend analysis and historical queries.
    """

    __tablename__ = "bike_snapshots"

    # Use TimescaleDB hypertable (composite primary key with time)
    time = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    bike_id = Column(String, ForeignKey("bikes.bike_id"), nullable=False, primary_key=True)

    # Location
    station_id = Column(String, ForeignKey("stations.id"), nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    # State
    is_reserved = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    current_range_meters = Column(Integer, nullable=True)
    vehicle_type_id = Column(String, nullable=True)

    __table_args__ = (
        Index('idx_bike_snapshots_time', 'time'),
        Index('idx_bike_snapshots_bike', 'bike_id', 'time'),
        Index('idx_bike_snapshots_station', 'station_id', 'time'),
    )

    def __repr__(self):
        return f"<BikeSnapshot(bike_id={self.bike_id}, time={self.time})>"
