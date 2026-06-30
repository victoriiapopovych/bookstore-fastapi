from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


client: AsyncIOMotorClient | None = None
database = None


async def connect_to_mongo():
    global client, database

    client = AsyncIOMotorClient(settings.MONGO_URL)
    database = client[settings.MONGO_DB_NAME]

    await database.command("ping")


async def close_mongo_connection():
    if client:
        client.close()