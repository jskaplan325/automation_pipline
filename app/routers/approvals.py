"""
Approval workflow routes.
"""
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.catalog import catalog_service
from app.database import get_db
from app.models import DeploymentRequest, RequestStatus
from app.services.ado_client import trigger_deployment
from app.services.email_service import send_approval_notification, send_rejection_notification
from app.services.teams_webhook import send_deployment_notification

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def approvals_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Dashboard showing pending approvals (approvers only)."""
    user = get_current_user(request)

    if not user.is_approver:
        raise HTTPException(status_code=403, detail="Approvers only")

    # Get pending requests
    result = await db.execute(
        select(DeploymentRequest)
        .where(DeploymentRequest.status == RequestStatus.PENDING_APPROVAL)
        .order_by(DeploymentRequest.created_at.asc())  # Oldest first
    )
    pending_requests = result.scalars().all()

    # Enrich with catalog info
    enriched_requests = []
    for req in pending_requests:
        catalog_item = catalog_service.get_by_id(req.catalog_item_id)
        enriched_requests.append({
            "request": req,
            "catalog_item": catalog_item,
        })

    # Get recently processed requests
    result = await db.execute(
        select(DeploymentRequest)
        .where(DeploymentRequest.status.in_([
            RequestStatus.APPROVED,
            RequestStatus.REJECTED,
            RequestStatus.DEPLOYING,
            RequestStatus.COMPLETED,
            RequestStatus.FAILED,
        ]))
        .order_by(DeploymentRequest.updated_at.desc())
        .limit(10)
    )
    recent_requests = result.scalars().all()

    enriched_recent = []
    for req in recent_requests:
        catalog_item = catalog_service.get_by_id(req.catalog_item_id)
        enriched_recent.append({
            "request": req,
            "catalog_item": catalog_item,
        })

    return templates.TemplateResponse(
        "approvals.html",
        {
            "request": request,
            "user": user,
            "pending_requests": enriched_requests,
            "recent_requests": enriched_recent,
        },
    )


@router.get("/{request_id}")
async def review_request(
    request: Request,
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Review a specific deployment request for approval."""
    user = get_current_user(request)

    if not user.is_approver:
        raise HTTPException(status_code=403, detail="Approvers only")

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment_request = result.scalar_one_or_none()

    if not deployment_request:
        raise HTTPException(status_code=404, detail="Request not found")

    catalog_item = catalog_service.get_by_id(deployment_request.catalog_item_id)

    return templates.TemplateResponse(
        "approval_review.html",
        {
            "request": request,
            "user": user,
            "deployment_request": deployment_request,
            "catalog_item": catalog_item,
        },
    )


@router.post("/{request_id}/approve")
async def approve_request(
    request: Request,
    request_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Approve a deployment request."""
    user = get_current_user(request)

    if not user.is_approver:
        raise HTTPException(status_code=403, detail="Approvers only")

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment_request = result.scalar_one_or_none()

    if not deployment_request:
        raise HTTPException(status_code=404, detail="Request not found")

    if deployment_request.status != RequestStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Request is not pending approval")

    # Update request status
    deployment_request.status = RequestStatus.APPROVED
    deployment_request.approved_by = user.email
    deployment_request.approved_at = datetime.utcnow()

    # Get catalog item for pipeline info
    catalog_item = catalog_service.get_by_id(deployment_request.catalog_item_id)

    # Try to trigger ADO pipeline
    if catalog_item and catalog_item.ado_pipeline.pipeline_id:
        try:
            build_info = await trigger_deployment(
                catalog_item.ado_pipeline,
                deployment_request.parameters,
            )
            deployment_request.ado_build_id = build_info.get("id")
            deployment_request.ado_build_url = build_info.get("url")
            deployment_request.status = RequestStatus.DEPLOYING
        except Exception as e:
            # Log error but don't fail the approval
            print(f"Failed to trigger ADO pipeline: {e}")
            # Status remains APPROVED, can retry pipeline trigger later

    await db.commit()

    # Send notifications (fire and forget - don't fail if notifications fail)
    try:
        template_name = catalog_item.name if catalog_item else deployment_request.catalog_item_id
        await send_approval_notification(
            requester_email=deployment_request.requester_email,
            template_name=template_name,
            request_id=deployment_request.id,
            approved_by=user.name,
        )
        await send_deployment_notification(
            request_id=deployment_request.id,
            requester_name=deployment_request.requester_name,
            template_name=template_name,
            status="started",
            approved_by=user.name,
        )
    except Exception as e:
        print(f"Failed to send notifications: {e}")

    return RedirectResponse(url="/approvals", status_code=302)


@router.post("/{request_id}/reject")
async def reject_request(
    request: Request,
    request_id: str,
    reason: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Reject a deployment request."""
    user = get_current_user(request)

    if not user.is_approver:
        raise HTTPException(status_code=403, detail="Approvers only")

    result = await db.execute(
        select(DeploymentRequest).where(DeploymentRequest.id == request_id)
    )
    deployment_request = result.scalar_one_or_none()

    if not deployment_request:
        raise HTTPException(status_code=404, detail="Request not found")

    if deployment_request.status != RequestStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Request is not pending approval")

    # Update request
    deployment_request.status = RequestStatus.REJECTED
    deployment_request.approved_by = user.email  # Reusing field for rejector
    deployment_request.approved_at = datetime.utcnow()
    deployment_request.rejection_reason = reason

    await db.commit()

    # Send rejection notification
    try:
        catalog_item = catalog_service.get_by_id(deployment_request.catalog_item_id)
        template_name = catalog_item.name if catalog_item else deployment_request.catalog_item_id
        await send_rejection_notification(
            requester_email=deployment_request.requester_email,
            template_name=template_name,
            request_id=deployment_request.id,
            rejected_by=user.name,
            reason=reason,
        )
    except Exception as e:
        print(f"Failed to send rejection notification: {e}")

    return RedirectResponse(url="/approvals", status_code=302)
