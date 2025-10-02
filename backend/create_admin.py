"""Create or update admin user with password admin123."""

import asyncio
import bcrypt
from app.database import AsyncSessionLocal
from app.repositories import UserRepository
from app.schemas.auth import UserRegister


async def create_admin():
    """Create or update admin user."""
    async with AsyncSessionLocal() as db:
        try:
            repo = UserRepository(db)

            # Check if admin exists
            admin = await repo.get_by_email("admin@velivert.com")

            if admin:
                print("Admin user already exists. Updating password...")
                # Update password directly using bcrypt
                password_bytes = "admin123".encode('utf-8')
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

                from sqlalchemy import update
                from app.models import User

                stmt = update(User).where(User.email == "admin@velivert.com").values(
                    hashed_password=hashed_password
                )
                await db.execute(stmt)
                await db.commit()
                print("✅ Admin password updated to: admin123")
            else:
                print("Creating new admin user...")
                user_data = UserRegister(
                    email="admin@velivert.com",
                    password="admin123",
                    full_name="Administrator",
                    role="admin"
                )
                await repo.create(user_data)
                await db.commit()
                print("✅ Admin user created successfully!")

            print("\nAdmin Credentials:")
            print("Email: admin@velivert.com")
            print("Password: admin123")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(create_admin())
