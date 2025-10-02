"""API endpoint to analyze historical bike movements from snapshots."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
import structlog

from app.database import get_db
from app.models import BikeSnapshot, BikeMovement, Bike
from app.services.bike_movement_tracker import BikeMovementTracker

router = APIRouter()
logger = structlog.get_logger()


@router.post("/analyze-historical")
async def analyze_historical_movements(
    hours: int = Query(24, ge=1, le=168, description="Hours to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze bike snapshots from the past and detect movements retroactively.

    This fills in missing movement records by comparing historical snapshots.
    """
    logger.info("historical_analysis_start", hours=hours)

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    # Get all bike snapshots in the time range, ordered by bike and time
    query = select(BikeSnapshot).where(
        BikeSnapshot.time >= start_time,
        BikeSnapshot.time <= end_time
    ).order_by(BikeSnapshot.bike_id, BikeSnapshot.time)

    result = await db.execute(query)
    snapshots = result.scalars().all()

    logger.info("snapshots_loaded", count=len(snapshots))

    # Group snapshots by bike
    bikes_snapshots = {}
    for snapshot in snapshots:
        if snapshot.bike_id not in bikes_snapshots:
            bikes_snapshots[snapshot.bike_id] = []
        bikes_snapshots[snapshot.bike_id].append(snapshot)

    tracker = BikeMovementTracker(db)
    movements_detected = 0

    # Analyze each bike's snapshot history
    for bike_id, bike_snapshots in bikes_snapshots.items():
        if len(bike_snapshots) < 2:
            continue

        # Compare consecutive snapshots
        for i in range(len(bike_snapshots) - 1):
            prev_snap = bike_snapshots[i]
            curr_snap = bike_snapshots[i + 1]

            # Calculate distance
            distance = tracker.calculate_distance(
                float(prev_snap.lat), float(prev_snap.lon),
                float(curr_snap.lat), float(curr_snap.lon)
            )

            # Check if movement occurred
            if distance > tracker.MOVEMENT_THRESHOLD or prev_snap.station_id != curr_snap.station_id:
                # Check if this movement already exists
                existing = await db.execute(
                    select(BikeMovement).where(
                        and_(
                            BikeMovement.bike_id == bike_id,
                            BikeMovement.detected_at >= prev_snap.time,
                            BikeMovement.detected_at <= curr_snap.time
                        )
                    )
                )

                if existing.scalar_one_or_none():
                    continue  # Movement already recorded

                # Determine movement type
                movement_type = "unknown"
                if prev_snap.station_id and not curr_snap.station_id:
                    movement_type = "pickup"
                elif not prev_snap.station_id and curr_snap.station_id:
                    movement_type = "dropoff"
                elif prev_snap.station_id and curr_snap.station_id:
                    movement_type = "relocation"
                else:
                    movement_type = "in_transit"

                # Create movement record
                movement = BikeMovement(
                    bike_id=bike_id,
                    from_station_id=prev_snap.station_id,
                    from_lat=float(prev_snap.lat),
                    from_lon=float(prev_snap.lon),
                    to_station_id=curr_snap.station_id,
                    to_lat=float(curr_snap.lat),
                    to_lon=float(curr_snap.lon),
                    movement_type=movement_type,
                    distance_meters=distance,
                    is_reserved=curr_snap.is_reserved,
                    is_disabled=curr_snap.is_disabled,
                    battery_range_meters=curr_snap.current_range_meters,
                    detected_at=curr_snap.time  # Use snapshot time
                )

                db.add(movement)
                movements_detected += 1

    await db.commit()

    logger.info("historical_analysis_complete", movements_detected=movements_detected)

    return {
        "success": True,
        "period_hours": hours,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "snapshots_analyzed": len(snapshots),
        "unique_bikes": len(bikes_snapshots),
        "movements_detected": movements_detected,
        "message": f"✅ Analyse historique terminée: {movements_detected} mouvements détectés"
    }
