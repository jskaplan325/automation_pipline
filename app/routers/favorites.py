"""
Favorites management routes.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.catalog import catalog_service
from app.database import get_db
from app.models import Favorite
from app.services.audit_service import log_favorite_added, log_favorite_removed

router = APIRouter()


@router.get("/")
async def get_favorites(request: Request, db: AsyncSession = Depends(get_db)):
    """Get current user's favorite catalog items."""
    user = get_current_user(request)

    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_email == user.email)
        .order_by(Favorite.created_at.desc())
    )
    favorites = result.scalars().all()

    # Enrich with catalog info
    enriched = []
    for fav in favorites:
        item = catalog_service.get_by_id(fav.catalog_item_id)
        if item:
            enriched.append({
                "id": fav.id,
                "catalog_item_id": fav.catalog_item_id,
                "catalog_item": item,
                "created_at": fav.created_at,
            })

    return JSONResponse(content={
        "favorites": [
            {
                "id": f["id"],
                "catalog_item_id": f["catalog_item_id"],
                "name": f["catalog_item"].name,
                "category": f["catalog_item"].category,
            }
            for f in enriched
        ]
    })


@router.post("/{item_id}")
async def add_favorite(
    request: Request,
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Add a catalog item to favorites."""
    user = get_current_user(request)

    # Check if item exists
    item = catalog_service.get_by_id(item_id)
    if not item:
        return JSONResponse(
            status_code=404,
            content={"error": "Catalog item not found"}
        )

    # Check if already favorited
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_email == user.email)
        .where(Favorite.catalog_item_id == item_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return JSONResponse(content={"status": "already_favorited", "id": existing.id})

    # Add favorite
    favorite = Favorite(
        user_email=user.email,
        catalog_item_id=item_id,
    )
    db.add(favorite)

    # Log action
    await log_favorite_added(
        db=db,
        user_email=user.email,
        user_name=user.name,
        catalog_item_id=item_id,
        request=request,
    )

    await db.commit()

    return JSONResponse(content={"status": "added", "id": favorite.id})


@router.delete("/{item_id}")
async def remove_favorite(
    request: Request,
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Remove a catalog item from favorites."""
    user = get_current_user(request)

    # Find and delete
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_email == user.email)
        .where(Favorite.catalog_item_id == item_id)
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        return JSONResponse(
            status_code=404,
            content={"error": "Favorite not found"}
        )

    await db.delete(favorite)

    # Log action
    await log_favorite_removed(
        db=db,
        user_email=user.email,
        user_name=user.name,
        catalog_item_id=item_id,
        request=request,
    )

    await db.commit()

    return JSONResponse(content={"status": "removed"})


@router.get("/check/{item_id}")
async def check_favorite(
    request: Request,
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Check if a catalog item is favorited by current user."""
    user = get_current_user(request)

    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_email == user.email)
        .where(Favorite.catalog_item_id == item_id)
    )
    favorite = result.scalar_one_or_none()

    return JSONResponse(content={"is_favorite": favorite is not None})
