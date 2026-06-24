from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import delete_user, get_users, update_user, serialize_user


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile_endpoint(current_user=Depends(get_current_user)):
    return serialize_user(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_my_profile_endpoint(
    user: UserUpdate,
    current_user=Depends(get_current_user),
):
    updated_user = await update_user(str(current_user["_id"]), user)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return updated_user


@router.delete("/me", response_model=UserResponse)
async def delete_my_account_endpoint(current_user=Depends(get_current_user)):
    deleted_user = await delete_user(str(current_user["_id"]))

    if not deleted_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return deleted_user