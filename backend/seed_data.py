"""Seed database with sample data for development and testing."""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
import random

from app.database import AsyncSessionLocal
from app.repositories import StationRepository, BikeRepository, InterventionRepository
from app.schemas.station import StationCreate
from app.schemas.intervention import InterventionCreate


async def seed_stations(db):
    """Seed stations data."""
    repo = StationRepository(db)

    stations = [
        {
            "id": "SE001",
            "name": "Place Jean Jaurès",
            "lat": Decimal("45.4397"),
            "lon": Decimal("4.3872"),
            "address": "Place Jean Jaurès, 42000 Saint-Étienne",
            "capacity": 20,
            "region_id": "SE",
            "rental_methods": ["CREDITCARD", "KEY"],
            "is_virtual_station": False
        },
        {
            "id": "SE002",
            "name": "Gare de Châteaucreux",
            "lat": Decimal("45.4446"),
            "lon": Decimal("4.3903"),
            "address": "Place de la Gare, 42000 Saint-Étienne",
            "capacity": 30,
            "region_id": "SE",
            "rental_methods": ["CREDITCARD", "KEY"],
            "is_virtual_station": False
        },
        {
            "id": "SE003",
            "name": "Hôtel de Ville",
            "lat": Decimal("45.4342"),
            "lon": Decimal("4.3901"),
            "address": "Place de l'Hôtel de Ville, 42000 Saint-Étienne",
            "capacity": 15,
            "region_id": "SE",
            "rental_methods": ["CREDITCARD", "KEY"],
            "is_virtual_station": False
        },
        {
            "id": "SE004",
            "name": "Campus Tréfilerie",
            "lat": Decimal("45.4574"),
            "lon": Decimal("4.3897"),
            "address": "23 Rue du Professeur Benoît Lauras, 42000 Saint-Étienne",
            "capacity": 25,
            "region_id": "SE",
            "rental_methods": ["CREDITCARD", "KEY"],
            "is_virtual_station": False
        },
        {
            "id": "SE005",
            "name": "Parc de l'Europe",
            "lat": Decimal("45.4285"),
            "lon": Decimal("4.3978"),
            "address": "Rue Eugène Beaune, 42000 Saint-Étienne",
            "capacity": 18,
            "region_id": "SE",
            "rental_methods": ["CREDITCARD", "KEY"],
            "is_virtual_station": False
        }
    ]

    for station_data in stations:
        station = StationCreate(**station_data)
        await repo.upsert(station)
        print(f"✅ Created station: {station.name}")

    # Add status snapshots for the last 24 hours
    now = datetime.utcnow()
    for i in range(48):  # Every 30 minutes for 24 hours
        snapshot_time = now - timedelta(minutes=30 * i)

        for station_data in stations:
            capacity = station_data["capacity"]
            # Simulate realistic occupancy patterns
            hour = snapshot_time.hour

            # More bikes available during night (3am-6am), fewer during day
            if 3 <= hour <= 6:
                bikes_available = random.randint(int(capacity * 0.7), capacity)
            elif 8 <= hour <= 10 or 17 <= hour <= 19:  # Rush hours
                bikes_available = random.randint(0, int(capacity * 0.3))
            else:
                bikes_available = random.randint(int(capacity * 0.3), int(capacity * 0.7))

            await repo.store_status_snapshot(
                station_id=station_data["id"],
                timestamp=snapshot_time,
                status_data={
                    "num_bikes_available": bikes_available,
                    "num_bikes_disabled": random.randint(0, 2),
                    "num_docks_available": capacity - bikes_available,
                    "num_docks_disabled": 0,
                    "is_installed": True,
                    "is_renting": True,
                    "is_returning": True,
                    "last_reported": snapshot_time
                }
            )

    print(f"✅ Created {len(stations) * 48} status snapshots")


async def seed_bikes(db):
    """Seed bikes data."""
    repo = BikeRepository(db)

    stations = ["SE001", "SE002", "SE003", "SE004", "SE005"]

    for i in range(50):
        bike_data = {
            "bike_id": f"BIKE{i+1:03d}",
            "vehicle_type_id": "CLASSIC",
            "current_station_id": random.choice(stations) if i < 40 else None,
            "lat": Decimal(f"{45.43 + random.uniform(0, 0.03):.6f}"),
            "lon": Decimal(f"{4.38 + random.uniform(0, 0.03):.6f}"),
            "is_reserved": False,
            "is_disabled": random.random() < 0.05,  # 5% disabled
            "current_range_meters": random.randint(5000, 30000) if random.random() < 0.5 else None,
        }

        await repo.upsert(bike_data)

    print(f"✅ Created 50 bikes")


async def seed_interventions(db):
    """Seed interventions data."""
    repo = InterventionRepository(db)

    intervention_types = ["repair", "relocation", "battery_swap", "maintenance", "cleaning"]
    priorities = ["low", "medium", "high", "urgent"]
    statuses = ["pending", "in_progress", "completed"]

    bikes = [f"BIKE{i+1:03d}" for i in range(50)]
    stations = ["SE001", "SE002", "SE003", "SE004", "SE005"]

    now = datetime.utcnow()

    # Create 20 interventions
    for i in range(20):
        days_ago = random.randint(0, 7)
        created = now - timedelta(days=days_ago)

        status = random.choice(statuses)

        # Randomly decide: 70% bike intervention, 30% station intervention
        if random.random() < 0.7:
            # Bike intervention
            bike_id = random.choice(bikes)
            station_id = random.choice(stations) if random.random() < 0.3 else None
        else:
            # Station intervention
            bike_id = None
            station_id = random.choice(stations)

        print(f"Creating intervention {i+1}: bike_id={bike_id}, station_id={station_id}")

        intervention_data = InterventionCreate(
            station_id=station_id,  # Put station_id first
            bike_id=bike_id,
            intervention_type=random.choice(intervention_types),
            priority=random.choice(priorities),
            description=f"Intervention #{i+1}: {random.choice(intervention_types)}",
            scheduled_at=created + timedelta(hours=random.randint(1, 48))
        )

        intervention = await repo.create(intervention_data)

        # Update status for some interventions
        if status != "pending":
            from app.schemas.intervention import InterventionUpdate
            update_data = InterventionUpdate(
                status=status,
                started_at=created + timedelta(hours=1) if status in ["in_progress", "completed"] else None,
                completed_at=created + timedelta(hours=2) if status == "completed" else None,
                notes=f"Work performed by technician" if status == "completed" else None
            )
            await repo.update(intervention.id, update_data)

    print(f"✅ Created 20 interventions")


async def main():
    """Main seed function."""
    print("🌱 Starting database seeding...\n")

    async with AsyncSessionLocal() as db:
        try:
            await seed_stations(db)
            await seed_bikes(db)
            await seed_interventions(db)

            await db.commit()
            print("\n✅ Database seeding completed successfully!")
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error seeding database: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())