from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings
from app.db.mongodb import close_mongo_connection, connect_to_mongo

from app.api.health import router as health_router

from app.api.categories import router as categories_router
from app.api.authors import router as authors_router
from app.api.products import router as products_router
from app.api.bundles import router as bundles_router
from app.api.discounts import router as discounts_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router

from app.core.logging import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(categories_router)
app.include_router(authors_router)
app.include_router(products_router)
app.include_router(bundles_router)
app.include_router(discounts_router)
app.include_router(auth_router)
app.include_router(users_router)

@app.get("/")
async def root():
    return {"message": "Bookstore API is running"}