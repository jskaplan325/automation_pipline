"""
Audit log viewing routes.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import AuditLog, AuditAction

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def view_audit_log(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    action: str = Query(None),
    user_filter: str = Query(None),
    days: int = Query(30, ge=1, le=365),
):
    """View the audit log (approvers only)."""
    user = get_current_user(request)

    if not user.is_approver:
        # Non-approvers can only see their own actions
        user_filter = user.email

    # Build query
    query = select(AuditLog)

    # Filter by date range
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = query.where(AuditLog.timestamp >= cutoff)

    # Filter by action type
    if action:
        try:
            action_enum = AuditAction(action)
            query = query.where(AuditLog.action == action_enum)
        except ValueError:
            pass

    # Filter by user
    if user_filter:
        query = query.where(AuditLog.user_email == user_filter)

    # Order by timestamp descending
    query = query.order_by(AuditLog.timestamp.desc())

    # Pagination
    per_page = 50
    offset = (page - 1) * per_page

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()

    # Get page of results
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    logs = result.scalars().all()

    total_pages = (total_count + per_page - 1) // per_page

    # Get available actions for filter dropdown
    available_actions = [a.value for a in AuditAction]

    return templates.TemplateResponse(
        "audit_log.html",
        {
            "request": request,
            "user": user,
            "logs": logs,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "action_filter": action,
            "user_filter": user_filter,
            "days_filter": days,
            "available_actions": available_actions,
        },
    )


@router.get("/stats")
async def audit_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """Get audit statistics for dashboard."""
    user = get_current_user(request)

    if not user.is_approver:
        return {"error": "Approvers only"}

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Count by action type
    action_counts = {}
    for action in AuditAction:
        result = await db.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.timestamp >= cutoff)
            .where(AuditLog.action == action)
        )
        count = result.scalar()
        if count > 0:
            action_counts[action.value] = count

    # Count by user
    result = await db.execute(
        select(AuditLog.user_email, func.count())
        .where(AuditLog.timestamp >= cutoff)
        .group_by(AuditLog.user_email)
        .order_by(func.count().desc())
        .limit(10)
    )
    user_counts = {row[0]: row[1] for row in result.all()}

    return {
        "period_days": days,
        "action_counts": action_counts,
        "top_users": user_counts,
    }
