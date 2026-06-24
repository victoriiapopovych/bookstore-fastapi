from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token
from app.schemas.token import TokenResponse
from app.schemas.user import UserLogin, UserRegister, UserResponse
from app.services.user_service import authenticate_user, register_user


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_endpoint(user: UserRegister):
    created_user = await register_user(user)

    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    return created_user


@router.post("/login", response_model=TokenResponse)
async def login_endpoint(user: UserLogin):
    authenticated_user = await authenticate_user(user.email, user.password)

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        data={
            "sub": str(authenticated_user["_id"]),
            "role": authenticated_user["role"],
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }