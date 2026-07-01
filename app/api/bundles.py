from fastapi import APIRouter, Depends, status

from app.dependencies.auth import require_manager
from app.exceptions.bundle import BundleNotFoundError
from app.schemas.bundle import BundleCreate, BundleUpdate, BundleUserResponse, BundleManagerResponse, PaginatedBundleManagerResponse, PaginatedBundleUserResponse
from app.services.bundle_service import create_bundle, get_bundles, get_active_bundles, get_bundle_by_id, update_bundle, delete_bundle

from app.utils.pagination import PaginationParams


router = APIRouter(prefix="/bundles", tags=["Bundles"])


@router.post("/", response_model=BundleManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_bundle_endpoint(
    bundle: BundleCreate,
    current_user: dict = Depends(require_manager),
):
    return await create_bundle(bundle)


@router.get("/", response_model=PaginatedBundleUserResponse)
async def get_active_bundles_endpoint(
    pagination: PaginationParams = Depends(),
):
    return await get_active_bundles(pagination)


@router.get("/manager", response_model=PaginatedBundleManagerResponse)
async def get_bundles_manager_endpoint(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(require_manager),
):
    return await get_bundles(pagination)


@router.get("/manager/{bundle_id}", response_model=BundleManagerResponse)
async def get_bundle_manager_endpoint(
    bundle_id: str,
    current_user: dict = Depends(require_manager),
):
    return await get_bundle_by_id(bundle_id)


@router.get("/{bundle_id}", response_model=BundleUserResponse)
async def get_bundle_endpoint(bundle_id: str):
    bundle = await get_bundle_by_id(bundle_id)

    if not bundle["is_active"]:
        raise BundleNotFoundError

    return bundle


@router.patch("/{bundle_id}", response_model=BundleManagerResponse)
async def update_bundle_endpoint(
    bundle_id: str,
    bundle: BundleUpdate,
    current_user: dict = Depends(require_manager),
):
    return await update_bundle(bundle_id, bundle)


@router.delete("/{bundle_id}", response_model=BundleManagerResponse)
async def delete_bundle_endpoint(
    bundle_id: str,
    current_user: dict = Depends(require_manager),
):
    return await delete_bundle(bundle_id)