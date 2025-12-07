"""
Terraform Self-Service Portal - Main FastAPI Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db
from app.auth import get_current_user
from app.catalog import catalog_service
from app.routers import catalog, requests, approvals, favorites, templates as templates_router, operations, audit, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    catalog_service.reload()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.app_name,
    description="Self-service portal for Azure infrastructure deployments via Terraform",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(catalog.router, prefix="/catalog", tags=["Catalog"])
app.include_router(requests.router, prefix="/requests", tags=["Requests"])
app.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
app.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
app.include_router(templates_router.router, prefix="/templates", tags=["Templates"])
app.include_router(operations.router, prefix="/operations", tags=["Operations"])
app.include_router(audit.router, prefix="/audit", tags=["Audit"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/")
async def home(request: Request):
    """Home page - redirects to catalog."""
    user = get_current_user(request)
    items = catalog_service.get_all()
    categories = catalog_service.get_categories()

    return templates.TemplateResponse(
        "catalog.html",
        {
            "request": request,
            "user": user,
            "items": items,
            "categories": categories,
            "selected_category": None,
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


# -----------------------------------------------------------------
# Development utilities
# -----------------------------------------------------------------

@app.get("/dev/set-role/{role}")
async def set_mock_role(request: Request, role: str):
    """
    DEV ONLY: Set mock user role for testing.
    Valid roles: 'user', 'approver'

    This endpoint sets a cookie to switch between user and approver roles
    during development. Remove this in production when using Entra ID.
    """
    from fastapi.responses import RedirectResponse

    response = RedirectResponse(url="/", status_code=302)

    if role in ("user", "approver"):
        response.set_cookie("mock_role", role, max_age=86400)

    return response
