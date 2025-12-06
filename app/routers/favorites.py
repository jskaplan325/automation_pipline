"""
Favorites management routes.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.catalog import catalog_service
from app.database import get_db
from app.models import Favorite
from app.services.audit_service import log_favorite_added, log_favorite_removed

router = APIRouter()


def render_favorite_button(item_id: str, is_favorite: bool) -> str:
    """Render the favorite button HTML."""
    if is_favorite:
        return f'''
        <button
            hx-delete="/favorites/{item_id}"
            hx-swap="outerHTML"
            class="favorite-btn p-1 text-red-500 hover:text-red-600 transition-colors"
            title="Remove from favorites"
        >
            <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
        </button>
        '''
    else:
        return f'''
        <button
            hx-post="/favorites/{item_id}"
            hx-swap="outerHTML"
            class="favorite-btn p-1 text-gray-400 hover:text-red-500 transition-colors"
            title="Add to favorites"
        >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
        </button>
        '''


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
    is_htmx = request.headers.get("HX-Request") == "true"

    # Check if item exists
    item = catalog_service.get_by_id(item_id)
    if not item:
        if is_htmx:
            return HTMLResponse(content="<span class='text-red-500'>Not found</span>", status_code=404)
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
        if is_htmx:
            return HTMLResponse(content=render_favorite_button(item_id, True))
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

    if is_htmx:
        return HTMLResponse(content=render_favorite_button(item_id, True))
    return JSONResponse(content={"status": "added", "id": favorite.id})


@router.delete("/{item_id}")
async def remove_favorite(
    request: Request,
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Remove a catalog item from favorites."""
    user = get_current_user(request)
    is_htmx = request.headers.get("HX-Request") == "true"

    # Find and delete
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_email == user.email)
        .where(Favorite.catalog_item_id == item_id)
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        if is_htmx:
            return HTMLResponse(content=render_favorite_button(item_id, False))
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

    if is_htmx:
        return HTMLResponse(content=render_favorite_button(item_id, False))
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
