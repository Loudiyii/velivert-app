"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test cases for authentication endpoints."""

    async def test_register_user(self, client: AsyncClient, sample_user_data):
        """Test user registration endpoint."""
        response = await client.post("/api/auth/register", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert data["role"] == sample_user_data["role"]
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password

    async def test_register_duplicate_email(self, client: AsyncClient, sample_user_data):
        """Test registering with duplicate email."""
        # Register first user
        await client.post("/api/auth/register", json=sample_user_data)

        # Try to register again with same email
        response = await client.post("/api/auth/register", json=sample_user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_login_success(self, client: AsyncClient, sample_user_data):
        """Test successful login."""
        # Register user first
        await client.post("/api/auth/register", json=sample_user_data)

        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    async def test_login_wrong_password(self, client: AsyncClient, sample_user_data):
        """Test login with wrong password."""
        # Register user first
        await client.post("/api/auth/register", json=sample_user_data)

        # Login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "wrongpassword"
        }
        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }
        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, sample_user_data):
        """Test getting current user info."""
        # Register and login
        await client.post("/api/auth/register", json=sample_user_data)

        login_response = await client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/auth/me")

        assert response.status_code == 403  # Missing auth header


@pytest.mark.asyncio
class TestStationEndpoints:
    """Test cases for station endpoints."""

    async def test_get_current_status_empty(self, client: AsyncClient):
        """Test getting current status when no stations exist."""
        response = await client.get("/api/stations/current")

        assert response.status_code == 200
        assert response.json() == []

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
class TestInterventionEndpoints:
    """Test cases for intervention endpoints."""

    async def test_create_intervention(self, client: AsyncClient, sample_intervention_data):
        """Test creating an intervention."""
        response = await client.post(
            "/api/interventions/",
            json=sample_intervention_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["bike_id"] == sample_intervention_data["bike_id"]
        assert data["intervention_type"] == sample_intervention_data["intervention_type"]
        assert data["priority"] == sample_intervention_data["priority"]
        assert data["status"] == "pending"
        assert "id" in data

    async def test_create_intervention_invalid(self, client: AsyncClient):
        """Test creating intervention without required fields."""
        # Missing both bike_id and station_id
        invalid_data = {
            "intervention_type": "repair",
            "priority": "medium"
        }
        response = await client.post("/api/interventions/", json=invalid_data)

        assert response.status_code == 422  # Validation error

    async def test_get_all_interventions(self, client: AsyncClient, sample_intervention_data):
        """Test getting all interventions."""
        # Create an intervention first
        await client.post("/api/interventions/", json=sample_intervention_data)

        # Get all interventions
        response = await client.get("/api/interventions/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_update_intervention_status(self, client: AsyncClient, sample_intervention_data):
        """Test updating intervention status."""
        # Create intervention
        create_response = await client.post(
            "/api/interventions/",
            json=sample_intervention_data
        )
        intervention_id = create_response.json()["id"]

        # Update status
        update_data = {"status": "in_progress"}
        response = await client.patch(
            f"/api/interventions/{intervention_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"


@pytest.mark.asyncio
class TestAnalyticsEndpoints:
    """Test cases for analytics endpoints."""

    async def test_get_idle_bikes(self, client: AsyncClient):
        """Test getting idle bikes."""
        response = await client.get(
            "/api/analytics/bikes/idle-detection",
            params={"threshold_hours": 24}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
