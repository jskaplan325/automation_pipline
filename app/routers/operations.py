"""
Operations routes for destroy and scale requests.
"""
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.catalog import catalog_service
from app.database import get_db
from app.models import DeploymentRequest, RequestStatus, RequestType
from app.services.audit_service import log_destroy_requested, log_scale_requested

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def is_htmx_request(request: Request) -> bool:
    """Check if request is from HTMX."""
    return request.headers.get("HX-Request") == "true"


@router.get("/active")
async def list_active_deployments(request: Request, db: AsyncSession = Depends(get_db)):
    """List current user's active deployments that can be managed."""
    user = get_current_user(request)

    result = await db.execute(
        select(DeploymentRequest)
        .where(DeploymentRequest.requester_email == user.email)
        .where(DeploymentRequest.status == RequestStatus.COMPLETED)
        .where(DeploymentRequest.request_type == RequestType.DEPLOY)
        .order_by(DeploymentRequest.created_at.desc())
    )
    deployments = result.scalars().all()

    # Enrich with catalog info
    enriched = []
    for dep in deployments:
        item = catalog_service.get_by_id(dep.catalog_item_id)
        enriched.append({
            "deployment": dep,
            "catalog_item": item,
        })

    return templates.TemplateResponse(
        "active_deployments.html",
        {
            "request": request,
            "user": user,
            "deployments": enriched,
        },
    )


@router.get("/destroy/{request_id}/modal")
async def destroy_modal(
    request: Request,
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return destroy confirmation modal (HTMX)."""
    user = get_current_user(request)

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if deployment.requester_email != user.email:
        raise HTTPException(status_code=403, detail="Not your deployment")

    if not deployment.can_destroy:
        raise HTTPException(status_code=400, detail="Deployment cannot be destroyed")

    item = catalog_service.get_by_id(deployment.catalog_item_id)

    return templates.TemplateResponse(
        "partials/destroy_modal.html",
        {
            "request": request,
            "deployment": deployment,
            "catalog_item": item,
        },
    )


@router.get("/destroy/{request_id}")
async def destroy_form(
    request: Request,
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Show form to request destruction of a deployment."""
    user = get_current_user(request)

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if deployment.requester_email != user.email:
        raise HTTPException(status_code=403, detail="Not your deployment")

    if not deployment.can_destroy:
        raise HTTPException(status_code=400, detail="Deployment cannot be destroyed")

    item = catalog_service.get_by_id(deployment.catalog_item_id)

    return templates.TemplateResponse(
        "destroy_form.html",
        {
            "request": request,
            "user": user,
            "deployment": deployment,
            "catalog_item": item,
        },
    )


@router.post("/destroy/{request_id}")
async def create_destroy_request(
    request: Request,
    request_id: str,
    reason: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """Create a destroy request for an existing deployment."""
    user = get_current_user(request)

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if deployment.requester_email != user.email:
        raise HTTPException(status_code=403, detail="Not your deployment")

    if not deployment.can_destroy:
        raise HTTPException(status_code=400, detail="Deployment cannot be destroyed")

    # Create destroy request
    destroy_request = DeploymentRequest(
        catalog_item_id=deployment.catalog_item_id,
        requester_email=user.email,
        requester_name=user.name,
        parameters={"original_request_id": request_id, "reason": reason},
        request_type=RequestType.DESTROY,
        status=RequestStatus.PENDING_APPROVAL,
        parent_request_id=request_id,
        cost_center=deployment.cost_center,
        environment_type=deployment.environment_type,
        project_code=deployment.project_code,
    )

    db.add(destroy_request)

    # Log action
    await log_destroy_requested(
        db=db,
        user_email=user.email,
        user_name=user.name,
        request_id=destroy_request.id,
        original_request_id=request_id,
        request=request,
    )

    await db.commit()

    # For HTMX requests, return success modal
    if is_htmx_request(request):
        return templates.TemplateResponse(
            "partials/destroy_success.html",
            {
                "request": request,
                "request_id": destroy_request.id,
            },
        )

    return RedirectResponse(url=f"/requests/{destroy_request.id}", status_code=302)


@router.get("/scale/{request_id}")
async def scale_form(
    request: Request,
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Show form to request scaling of a deployment."""
    user = get_current_user(request)

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if deployment.requester_email != user.email:
        raise HTTPException(status_code=403, detail="Not your deployment")

    if not deployment.can_scale:
        raise HTTPException(status_code=400, detail="Deployment cannot be scaled")

    item = catalog_service.get_by_id(deployment.catalog_item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")

    # Get current size from parameters
    current_size = deployment.parameters.get("size", "unknown")

    return templates.TemplateResponse(
        "scale_form.html",
        {
            "request": request,
            "user": user,
            "deployment": deployment,
            "catalog_item": item,
            "current_size": current_size,
        },
    )


@router.post("/scale/{request_id}")
async def create_scale_request(
    request: Request,
    request_id: str,
    new_size: str = Form(...),
    reason: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """Create a scale request for an existing deployment."""
    user = get_current_user(request)

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    if deployment.requester_email != user.email:
        raise HTTPException(status_code=403, detail="Not your deployment")

    if not deployment.can_scale:
        raise HTTPException(status_code=400, detail="Deployment cannot be scaled")

    current_size = deployment.parameters.get("size", "unknown")

    if new_size == current_size:
        raise HTTPException(status_code=400, detail="New size must be different from current size")

    # Create scale request with updated parameters
    new_parameters = deployment.parameters.copy()
    new_parameters["size"] = new_size

    scale_request = DeploymentRequest(
        catalog_item_id=deployment.catalog_item_id,
        requester_email=user.email,
        requester_name=user.name,
        parameters=new_parameters,
        request_type=RequestType.SCALE,
        status=RequestStatus.PENDING_APPROVAL,
        parent_request_id=request_id,
        previous_size=current_size,
        new_size=new_size,
        cost_center=deployment.cost_center,
        environment_type=deployment.environment_type,
        project_code=deployment.project_code,
    )

    db.add(scale_request)

    # Log action
    await log_scale_requested(
        db=db,
        user_email=user.email,
        user_name=user.name,
        request_id=scale_request.id,
        original_request_id=request_id,
        previous_size=current_size,
        new_size=new_size,
        request=request,
    )

    await db.commit()

    return RedirectResponse(url=f"/requests/{scale_request.id}", status_code=302)
