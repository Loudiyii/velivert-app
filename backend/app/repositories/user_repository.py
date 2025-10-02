"""Repository for User data access."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models import User
from app.schemas.auth import UserRegister
from app.services.auth_service import AuthService

logger = structlog.get_logger()


class UserRepository:
    """Repository handling all database operations for users."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email address

        Returns:
            User object or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: UserRegister) -> User:
        """
        Create a new user.

        Args:
            user_data: User registration data

        Returns:
            Created User object
        """
        # Hash password
        hashed_password = AuthService.hash_password(user_data.password)

        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        logger.info("user_created", user_id=str(user.id), email=user.email, role=user.role)

        return user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User object if authenticated, None otherwise
        """
        user = await self.get_by_email(email)

        if not user:
            logger.warning("authentication_failed", email=email, reason="user_not_found")
            return None

        if not user.is_active:
            logger.warning("authentication_failed", email=email, reason="user_inactive")
            return None

        if not AuthService.verify_password(password, user.hashed_password):
            logger.warning("authentication_failed", email=email, reason="invalid_password")
            return None

        logger.info("authentication_successful", user_id=str(user.id), email=email)
        return user
