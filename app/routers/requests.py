"""
Deployment request routes.
"""
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, User
from app.catalog import catalog_service
from app.database import get_db
from app.models import DeploymentRequest, RequestStatus
from app.services.email_service import send_approval_request_email

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def my_requests(request: Request, db: AsyncSession = Depends(get_db)):
    """List current user's deployment requests."""
    user = get_current_user(request)

    result = await db.execute(
        select(DeploymentRequest)
        .where(DeploymentRequest.requester_email == user.email)
        .order_by(DeploymentRequest.created_at.desc())
    )
    requests_list = result.scalars().all()

    # Enrich with catalog info
    enriched_requests = []
    for req in requests_list:
        catalog_item = catalog_service.get_by_id(req.catalog_item_id)
        enriched_requests.append({
            "request": req,
            "catalog_item": catalog_item,
        })

    return templates.TemplateResponse(
        "my_requests.html",
        {
            "request": request,
            "user": user,
            "requests": enriched_requests,
        },
    )


@router.get("/new/{item_id}")
async def new_request_form(request: Request, item_id: str):
    """Show the form to create a new deployment request."""
    user = get_current_user(request)
    item = catalog_service.get_by_id(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")

    return templates.TemplateResponse(
        "request_form.html",
        {
            "request": request,
            "user": user,
            "item": item,
        },
    )


@router.post("/new/{item_id}")
async def create_request(
    request: Request,
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Create a new deployment request."""
    user = get_current_user(request)
    item = catalog_service.get_by_id(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")

    # Parse form data
    form_data = await request.form()

    # Extract parameters based on catalog item definition
    parameters = {}
    for param in item.parameters:
        value = form_data.get(param.name)
        if param.required and not value:
            # Re-render form with error
            return templates.TemplateResponse(
                "request_form.html",
                {
                    "request": request,
                    "user": user,
                    "item": item,
                    "error": f"Required field '{param.label}' is missing",
                    "form_data": dict(form_data),
                },
                status_code=400,
            )
        if value:
            parameters[param.name] = value

    # Create the request
    deployment_request = DeploymentRequest(
        catalog_item_id=item_id,
        requester_email=user.email,
        requester_name=user.name,
        parameters=parameters,
        status=RequestStatus.PENDING_APPROVAL,
    )

    db.add(deployment_request)
    await db.commit()
    await db.refresh(deployment_request)

    # Send notification to approvers
    try:
        await send_approval_request_email(
            request_id=deployment_request.id,
            requester_name=user.name,
            requester_email=user.email,
            template_name=item.name,
            estimated_cost=item.estimated_monthly_cost_usd,
            parameters=parameters,
        )
    except Exception as e:
        print(f"Failed to send approval request email: {e}")

    return RedirectResponse(
        url=f"/requests/{deployment_request.id}",
        status_code=302,
    )


@router.get("/{request_id}/status")
async def get_request_status(
    request: Request,
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get request status row for HTMX polling."""
    user = get_current_user(request)

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment_request = result.scalar_one_or_none()

    if not deployment_request:
        raise HTTPException(status_code=404, detail="Request not found")

    catalog_item = catalog_service.get_by_id(deployment_request.catalog_item_id)

    return templates.TemplateResponse(
        "partials/request_row.html",
        {
            "request": deployment_request,
            "catalog_item": catalog_item,
        },
    )


@router.get("/{request_id}")
async def view_request(
    request: Request,
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """View details of a specific deployment request."""
    user = get_current_user(request)

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment_request = result.scalar_one_or_none()

    if not deployment_request:
        raise HTTPException(status_code=404, detail="Request not found")

    # Get catalog item for context
    catalog_item = catalog_service.get_by_id(deployment_request.catalog_item_id)

    return templates.TemplateResponse(
        "request_detail.html",
        {
            "request": request,
            "user": user,
            "deployment_request": deployment_request,
            "catalog_item": catalog_item,
        },
    )
