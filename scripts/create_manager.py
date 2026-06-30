import asyncio
from getpass import getpass

from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.schemas.user import UserRegister, UserRole
from app.services.user_service import register_user


async def create_manager():
    await connect_to_mongo()

    try:
        print("=== Create Manager ===")

        email = input("Email: ").strip().lower()
        password = getpass("Password: ")
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()

        manager = UserRegister(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        created_manager = await register_user(
            manager,
            role=UserRole.MANAGER,
        )

        if not created_manager:
            print("Manager with this email already exists.")
            return

        print("\nManager created successfully!")

    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(create_manager())