"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

from app.database import Base
from app.main import app
from app.api.dependencies import get_db


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_station_data():
    """Sample station data for testing."""
    return {
        "id": "TEST001",
        "name": "Test Station",
        "lat": 45.4397,
        "lon": 4.3872,
        "address": "123 Test St",
        "capacity": 20,
        "region_id": "TEST",
        "rental_methods": ["CREDITCARD"],
        "is_virtual_station": False
    }


@pytest.fixture
def sample_bike_data():
    """Sample bike data for testing."""
    return {
        "bike_id": "TESTBIKE001",
        "vehicle_type_id": "CLASSIC",
        "lat": 45.44,
        "lon": 4.39,
        "is_reserved": False,
        "is_disabled": False
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "role": "viewer"
    }


@pytest.fixture
def sample_intervention_data():
    """Sample intervention data for testing."""
    return {
        "bike_id": "TESTBIKE001",
        "intervention_type": "repair",
        "priority": "medium",
        "description": "Test repair intervention"
    }
