from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user, require_manager
from app.exceptions.user import CannotDeactivateSelfError
from app.schemas.user import UserSelfResponse, UserManagerResponse, UserUpdate, PaginatedUserManagerResponse
from app.services.user_service import serialize_user, get_users, get_user_by_id, update_user, deactivate_user

from app.utils.pagination import PaginationParams


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserSelfResponse)
async def get_my_profile_endpoint(current_user=Depends(get_current_user),):
    return serialize_user(current_user)


@router.patch("/me", response_model=UserSelfResponse)
async def update_my_profile_endpoint(user: UserUpdate, current_user=Depends(get_current_user),):
    return await update_user(
        str(current_user["_id"]),
        user,
    )


@router.get("/manager", response_model=PaginatedUserManagerResponse, dependencies=[Depends(require_manager)])
async def get_users_endpoint(
    pagination: PaginationParams = Depends(),
):
    return await get_users(pagination)


@router.get("/manager/{user_id}", response_model=UserManagerResponse, dependencies=[Depends(require_manager)],)
async def get_user_endpoint(user_id: str):
    return await get_user_by_id(user_id)


@router.delete("/manager/{user_id}", response_model=UserManagerResponse, dependencies=[Depends(require_manager)],)
async def deactivate_user_endpoint(user_id: str, current_user=Depends(get_current_user),):
    if str(current_user["_id"]) == user_id:
        raise CannotDeactivateSelfError

    return await deactivate_user(user_id)