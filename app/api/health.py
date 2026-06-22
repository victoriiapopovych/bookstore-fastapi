from fastapi import APIRouter, HTTPException, status

from app.db import mongodb

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    try:
        await mongodb.database.command("ping")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "database": "disconnected",
            },
        )

    return {
        "status": "ok",
        "database": "connected",
    }
