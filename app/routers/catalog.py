"""
Catalog browsing routes.
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.catalog import catalog_service
from app.database import get_db
from app.models import Favorite

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_user_favorites(user_email: str, db: AsyncSession) -> set:
    """Get set of favorited catalog item IDs for a user."""
    result = await db.execute(
        select(Favorite.catalog_item_id)
        .where(Favorite.user_email == user_email)
    )
    return {row[0] for row in result.fetchall()}


@router.get("/")
async def list_catalog(
    request: Request,
    category: str = None,
    search: str = None,
    favorites: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all catalog items with optional filtering."""
    user = get_current_user(request)
    is_htmx = request.headers.get("HX-Request") == "true"

    # Get user's favorites
    user_favorites = await get_user_favorites(user.email, db)
    show_favorites = favorites == "1"

    if search:
        items = catalog_service.search(search)
    elif category:
        items = catalog_service.get_by_category(category)
    else:
        items = catalog_service.get_all()

    # Filter to only favorites if requested
    if show_favorites:
        items = [item for item in items if item.id in user_favorites]

    categories = catalog_service.get_categories()

    # For HTMX requests, return just the grid partial
    if is_htmx:
        return templates.TemplateResponse(
            "partials/catalog_grid.html",
            {
                "request": request,
                "user": user,
                "items": items,
                "favorites": user_favorites,
                "search_query": search or "",
                "show_favorites": show_favorites,
            },
        )

    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "user": user,
            "items": items,
            "categories": categories,
            "selected_category": category,
            "search_query": search or "",
            "favorites": user_favorites,
            "show_favorites": show_favorites,
        },
    )


@router.get("/{item_id}")
async def get_catalog_item(request: Request, item_id: str):
    """View details of a specific catalog item."""
    user = get_current_user(request)
    item = catalog_service.get_by_id(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")

    return templates.TemplateResponse(
        "catalog_item.html",
        {
            "request": request,
            "user": user,
            "item": item,
        },
    )
