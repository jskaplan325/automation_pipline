"""
Catalog browsing routes.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates

from app.auth import get_current_user
from app.catalog import catalog_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def list_catalog(request: Request, category: str = None, search: str = None):
    """List all catalog items with optional filtering."""
    user = get_current_user(request)

    if search:
        items = catalog_service.search(search)
    elif category:
        items = catalog_service.get_by_category(category)
    else:
        items = catalog_service.get_all()

    categories = catalog_service.get_categories()

    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "user": user,
            "items": items,
            "categories": categories,
            "selected_category": category,
            "search_query": search or "",
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
