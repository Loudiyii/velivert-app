"""Unit tests for repositories."""

import pytest
from datetime import datetime

from app.repositories import StationRepository, BikeRepository, UserRepository, InterventionRepository
from app.schemas.station import StationCreate
from app.schemas.auth import UserRegister
from app.schemas.intervention import InterventionCreate


@pytest.mark.asyncio
class TestStationRepository:
    """Test cases for StationRepository."""

    async def test_create_station(self, db_session, sample_station_data):
        """Test creating a station."""
        repo = StationRepository(db_session)
        station_create = StationCreate(**sample_station_data)

        station = await repo.create(station_create)
        await db_session.commit()

        assert station.id == sample_station_data["id"]
        assert station.name == sample_station_data["name"]
        assert float(station.lat) == sample_station_data["lat"]
        assert float(station.lon) == sample_station_data["lon"]
        assert station.capacity == sample_station_data["capacity"]

    async def test_get_station_by_id(self, db_session, sample_station_data):
        """Test retrieving a station by ID."""
        repo = StationRepository(db_session)
        station_create = StationCreate(**sample_station_data)

        created_station = await repo.create(station_create)
        await db_session.commit()

        found_station = await repo.get_by_id(sample_station_data["id"])

        assert found_station is not None
        assert found_station.id == created_station.id
        assert found_station.name == created_station.name

    async def test_get_station_by_id_not_found(self, db_session):
        """Test retrieving a non-existent station."""
        repo = StationRepository(db_session)
        station = await repo.get_by_id("NONEXISTENT")

        assert station is None

    async def test_get_all_stations(self, db_session, sample_station_data):
        """Test retrieving all stations."""
        repo = StationRepository(db_session)

        # Create multiple stations
        for i in range(3):
            data = sample_station_data.copy()
            data["id"] = f"TEST{i:03d}"
            station_create = StationCreate(**data)
            await repo.create(station_create)

        await db_session.commit()

        stations = await repo.get_all(skip=0, limit=10)

        assert len(stations) == 3

    async def test_upsert_station_create(self, db_session, sample_station_data):
        """Test upsert creates new station when it doesn't exist."""
        repo = StationRepository(db_session)
        station_create = StationCreate(**sample_station_data)

        station = await repo.upsert(station_create)
        await db_session.commit()

        assert station.id == sample_station_data["id"]

    async def test_upsert_station_update(self, db_session, sample_station_data):
        """Test upsert updates existing station."""
        repo = StationRepository(db_session)
        station_create = StationCreate(**sample_station_data)

        # Create initial station
        await repo.create(station_create)
        await db_session.commit()

        # Update via upsert
        updated_data = sample_station_data.copy()
        updated_data["name"] = "Updated Station Name"
        station_update = StationCreate(**updated_data)

        updated_station = await repo.upsert(station_update)
        await db_session.commit()

        assert updated_station.name == "Updated Station Name"


@pytest.mark.asyncio
class TestBikeRepository:
    """Test cases for BikeRepository."""

    async def test_create_bike(self, db_session, sample_bike_data):
        """Test creating a bike."""
        repo = BikeRepository(db_session)

        bike = await repo.upsert(sample_bike_data)
        await db_session.commit()

        assert bike.bike_id == sample_bike_data["bike_id"]
        assert float(bike.lat) == sample_bike_data["lat"]
        assert bike.is_disabled == sample_bike_data["is_disabled"]

    async def test_get_bike_by_id(self, db_session, sample_bike_data):
        """Test retrieving a bike by ID."""
        repo = BikeRepository(db_session)

        created_bike = await repo.upsert(sample_bike_data)
        await db_session.commit()

        found_bike = await repo.get_by_id(sample_bike_data["bike_id"])

        assert found_bike is not None
        assert found_bike.bike_id == created_bike.bike_id


@pytest.mark.asyncio
class TestUserRepository:
    """Test cases for UserRepository."""

    async def test_create_user(self, db_session, sample_user_data):
        """Test creating a user."""
        repo = UserRepository(db_session)
        user_register = UserRegister(**sample_user_data)

        user = await repo.create(user_register)
        await db_session.commit()

        assert user.email == sample_user_data["email"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.role == sample_user_data["role"]
        assert user.is_active is True
        # Password should be hashed
        assert user.hashed_password != sample_user_data["password"]

    async def test_get_user_by_email(self, db_session, sample_user_data):
        """Test retrieving a user by email."""
        repo = UserRepository(db_session)
        user_register = UserRegister(**sample_user_data)

        created_user = await repo.create(user_register)
        await db_session.commit()

        found_user = await repo.get_by_email(sample_user_data["email"])

        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == created_user.email

    async def test_authenticate_user_success(self, db_session, sample_user_data):
        """Test successful user authentication."""
        repo = UserRepository(db_session)
        user_register = UserRegister(**sample_user_data)

        await repo.create(user_register)
        await db_session.commit()

        authenticated_user = await repo.authenticate(
            sample_user_data["email"],
            sample_user_data["password"]
        )

        assert authenticated_user is not None
        assert authenticated_user.email == sample_user_data["email"]

    async def test_authenticate_user_wrong_password(self, db_session, sample_user_data):
        """Test authentication with wrong password."""
        repo = UserRepository(db_session)
        user_register = UserRegister(**sample_user_data)

        await repo.create(user_register)
        await db_session.commit()

        authenticated_user = await repo.authenticate(
            sample_user_data["email"],
            "wrongpassword"
        )

        assert authenticated_user is None

    async def test_authenticate_user_not_found(self, db_session):
        """Test authentication with non-existent user."""
        repo = UserRepository(db_session)

        authenticated_user = await repo.authenticate(
            "nonexistent@example.com",
            "anypassword"
        )

        assert authenticated_user is None


@pytest.mark.asyncio
class TestInterventionRepository:
    """Test cases for InterventionRepository."""

    async def test_create_intervention(self, db_session, sample_intervention_data):
        """Test creating an intervention."""
        repo = InterventionRepository(db_session)
        intervention_create = InterventionCreate(**sample_intervention_data)

        intervention = await repo.create(intervention_create)
        await db_session.commit()

        assert intervention.bike_id == sample_intervention_data["bike_id"]
        assert intervention.intervention_type == sample_intervention_data["intervention_type"]
        assert intervention.priority == sample_intervention_data["priority"]
        assert intervention.status == "pending"

    async def test_get_intervention_by_id(self, db_session, sample_intervention_data):
        """Test retrieving an intervention by ID."""
        repo = InterventionRepository(db_session)
        intervention_create = InterventionCreate(**sample_intervention_data)

        created = await repo.create(intervention_create)
        await db_session.commit()

        found = await repo.get_by_id(str(created.id))

        assert found is not None
        assert found.id == created.id

    async def test_get_all_interventions(self, db_session, sample_intervention_data):
        """Test retrieving all interventions."""
        repo = InterventionRepository(db_session)

        # Create multiple interventions
        for i in range(3):
            data = sample_intervention_data.copy()
            intervention_create = InterventionCreate(**data)
            await repo.create(intervention_create)

        await db_session.commit()

        interventions = await repo.get_all(skip=0, limit=10)

        assert len(interventions) >= 3
