from fastapi import APIRouter, status, HTTPException

from app.schemas.bundle import BundleCreate, BundleResponse, BundleUpdate
from app.services.bundle_service import create_bundle, get_bundles, get_bundle_by_id, update_bundle, delete_bundle


router = APIRouter(prefix="/bundles", tags=["Bundles"])


@router.post("/", response_model=BundleResponse, status_code=status.HTTP_201_CREATED)
async def create_bundle_endpoint(bundle: BundleCreate):
    created_bundle = await create_bundle(bundle)

    if not created_bundle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product_ids",
        )

    return created_bundle


@router.get("/", response_model=list[BundleResponse])
async def get_bundles_endpoint():
    return await get_bundles()


@router.get("/{bundle_id}", response_model=BundleResponse)
async def get_bundle_endpoint(bundle_id: str):
    bundle = await get_bundle_by_id(bundle_id)

    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle not found",
        )

    return bundle


@router.patch("/{bundle_id}", response_model=BundleResponse)
async def update_bundle_endpoint(bundle_id: str, bundle: BundleUpdate):
    updated_bundle = await update_bundle(bundle_id, bundle)

    if not updated_bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle not found or invalid product_ids",
        )

    return updated_bundle


@router.delete("/{bundle_id}", response_model=BundleResponse)
async def delete_bundle_endpoint(bundle_id: str):
    deleted_bundle = await delete_bundle(bundle_id)

    if not deleted_bundle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle not found",
        )

    return deleted_bundle