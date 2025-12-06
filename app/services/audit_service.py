"""
Audit logging service for tracking all actions in the system.
"""
from datetime import datetime
from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, AuditAction


async def log_action(
    db: AsyncSession,
    user_email: str,
    user_name: str,
    action: AuditAction,
    request_id: Optional[str] = None,
    catalog_item_id: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """
    Log an auditable action to the database.

    Args:
        db: Database session
        user_email: Email of user performing the action
        user_name: Name of user performing the action
        action: Type of action being performed
        request_id: Related deployment request ID (optional)
        catalog_item_id: Related catalog item ID (optional)
        details: Additional details as dict (optional)
        request: FastAPI request for IP/user agent (optional)
    """
    ip_address = None
    user_agent = None

    if request:
        # Get client IP (handle proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None

        user_agent = request.headers.get("User-Agent", "")[:500]

    audit_log = AuditLog(
        user_email=user_email,
        user_name=user_name,
        action=action,
        request_id=request_id,
        catalog_item_id=catalog_item_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(audit_log)
    await db.flush()  # Get the ID without committing

    return audit_log


async def log_request_created(
    db: AsyncSession,
    user_email: str,
    user_name: str,
    request_id: str,
    catalog_item_id: str,
    parameters: dict,
    request: Optional[Request] = None,
) -> AuditLog:
    """Log a new deployment request."""
    return await log_action(
        db=db,
        user_email=user_email,
        user_name=user_name,
        action=AuditAction.REQUEST_CREATED,
        request_id=request_id,
        catalog_item_id=catalog_item_id,
        details={"parameters": parameters},
        request=request,
    )


async def log_request_approved(
    db: AsyncSession,
    user_email: str,
    user_name: str,
    request_id: str,
    request: Optional[Request] = None,
) -> AuditLog:
    """Log a request approval."""
    return await log_action(
        db=db,
        user_email=user_email,
        user_name=user_name,
        action=AuditAction.REQUEST_APPROVED,
        request_id=request_id,
        request=request,
    )


async def log_request_rejected(
    db: AsyncSession,
    user_email: str,
    user_name: str,
    request_id: str,
    reason: str,
    request: Optional[Request] = None,
) -> AuditLog:
    """Log a request rejection."""
    return await log_action(
        db=db,
        user_email=user_email,
        user_name=user_name,
        action=AuditAction.REQUEST_REJECTED,
        request_id=request_id,
        details={"reason": reason},
        request=request,
    )


async def log_destroy_requested(
    db: AsyncSession,
    user_email: str,
    user_name: str,
    request_id: str,
    original_request_id: str,
    request: Optional[Request] = None,
) -> AuditLog:
    """Log a destroy request."""
    return await log_action(
        db=db,
        user_email=user_email,
        user_name=user_name,
        action=AuditAction.DESTROY_REQUESTED,
        request_id=request_id,
        details={"original_request_id": original_request_id},
        request=request,
    )


async def log_scale_requested(
    db: AsyncSession,
    user_email: str,
    user_name: str,
    request_id: str,
    original_request_id: str,
    previous_size: str,
    new_size: str,
    request: Optional[Request] = None,
) -> AuditLog:
    """Log a scale request."""
    return await log_action(
        db=db,
        user_email=user_email,
        user_name=user_name,
        action=AuditAction.SCALE_REQUESTED,
        request_id=request_id,
        details={
            "original_request_id": original_request_id,
            "previous_size": previous_size,
            "new_size": new_size,
        },
        request=request,
    )


async def log_favorite_added(
    db: AsyncSession,
    user_email: str,
    user_name: str,
    catalog_item_id: str,
    request: Optional[Request] = None,
) -> AuditLog:
    """Log adding a favorite."""
    return await log_action(
        db=db,
        user_email=user_email,
        user_name=user_name,
        action=AuditAction.FAVORITE_ADDED,
        catalog_item_id=catalog_item_id,
        request=request,
    )


async def log_favorite_removed(
    db: AsyncSession,
    user_email: str,
    user_name: str,
    catalog_item_id: str,
    request: Optional[Request] = None,
) -> AuditLog:
    """Log removing a favorite."""
    return await log_action(
        db=db,
        user_email=user_email,
        user_name=user_name,
        action=AuditAction.FAVORITE_REMOVED,
        catalog_item_id=catalog_item_id,
        request=request,
    )


async def log_template_saved(
    db: AsyncSession,
    user_email: str,
    user_name: str,
    catalog_item_id: str,
    template_name: str,
    request: Optional[Request] = None,
) -> AuditLog:
    """Log saving a request template."""
    return await log_action(
        db=db,
        user_email=user_email,
        user_name=user_name,
        action=AuditAction.TEMPLATE_SAVED,
        catalog_item_id=catalog_item_id,
        details={"template_name": template_name},
        request=request,
    )
