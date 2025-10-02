"""Unit tests for AuthService."""

import pytest
from uuid import uuid4
from datetime import timedelta

from app.services.auth_service import AuthService


class TestAuthService:
    """Test cases for AuthService."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash prefix

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """Test JWT token creation."""
        user_id = uuid4()
        email = "test@example.com"
        role = "viewer"

        token = AuthService.create_access_token(user_id, email, role)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiration(self):
        """Test JWT token creation with custom expiration."""
        user_id = uuid4()
        email = "test@example.com"
        role = "admin"
        expires_delta = timedelta(minutes=60)

        token = AuthService.create_access_token(
            user_id, email, role, expires_delta
        )

        assert token is not None
        assert isinstance(token, str)

    def test_decode_token_valid(self):
        """Test decoding a valid JWT token."""
        user_id = uuid4()
        email = "test@example.com"
        role = "technician"

        token = AuthService.create_access_token(user_id, email, role)
        token_data = AuthService.decode_token(token)

        assert token_data is not None
        assert token_data.user_id == user_id
        assert token_data.email == email
        assert token_data.role == role

    def test_decode_token_invalid(self):
        """Test decoding an invalid JWT token."""
        invalid_token = "invalid.token.string"
        token_data = AuthService.decode_token(invalid_token)

        assert token_data is None

    def test_decode_token_expired(self):
        """Test decoding an expired JWT token."""
        user_id = uuid4()
        email = "test@example.com"
        role = "viewer"

        # Create token with negative expiration (already expired)
        expires_delta = timedelta(seconds=-1)
        token = AuthService.create_access_token(
            user_id, email, role, expires_delta
        )

        token_data = AuthService.decode_token(token)

        # Expired token should return None
        assert token_data is None

    def test_password_hash_is_random(self):
        """Test that hashing the same password twice produces different hashes."""
        password = "samepassword"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

        # But both should verify correctly
        assert AuthService.verify_password(password, hash1) is True
        assert AuthService.verify_password(password, hash2) is True
