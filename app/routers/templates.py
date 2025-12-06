"""
Request templates management routes.
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.catalog import catalog_service
from app.database import get_db
from app.models import RequestTemplate
from app.services.audit_service import log_template_saved

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def list_templates(request: Request, db: AsyncSession = Depends(get_db)):
    """List current user's saved request templates."""
    user = get_current_user(request)

    result = await db.execute(
        select(RequestTemplate)
        .where(RequestTemplate.user_email == user.email)
        .order_by(RequestTemplate.updated_at.desc())
    )
    user_templates = result.scalars().all()

    # Enrich with catalog info
    enriched = []
    for tmpl in user_templates:
        item = catalog_service.get_by_id(tmpl.catalog_item_id)
        enriched.append({
            "template": tmpl,
            "catalog_item": item,
        })

    return templates.TemplateResponse(
        "templates_list.html",
        {
            "request": request,
            "user": user,
            "templates": enriched,
        },
    )


@router.get("/new/{item_id}")
async def new_template_form(request: Request, item_id: str):
    """Show form to create a new template from a catalog item."""
    user = get_current_user(request)
    item = catalog_service.get_by_id(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")

    return templates.TemplateResponse(
        "template_form.html",
        {
            "request": request,
            "user": user,
            "item": item,
            "template": None,
            "mode": "create",
        },
    )


@router.post("/new/{item_id}")
async def create_template(
    request: Request,
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Create a new request template."""
    user = get_current_user(request)
    item = catalog_service.get_by_id(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")

    form_data = await request.form()

    # Extract template metadata
    template_name = form_data.get("template_name", "").strip()
    template_description = form_data.get("template_description", "").strip()

    if not template_name:
        return templates.TemplateResponse(
            "template_form.html",
            {
                "request": request,
                "user": user,
                "item": item,
                "template": None,
                "mode": "create",
                "error": "Template name is required",
            },
            status_code=400,
        )

    # Extract parameters
    parameters = {}
    for param in item.parameters:
        value = form_data.get(param.name)
        if value:
            parameters[param.name] = value

    # Extract default tags
    cost_center = form_data.get("cost_center", "").strip() or None
    environment_type = form_data.get("environment_type", "").strip() or None
    project_code = form_data.get("project_code", "").strip() or None
    expiration_days = form_data.get("expiration_days", "").strip()
    expiration_days = int(expiration_days) if expiration_days else None

    # Create template
    tmpl = RequestTemplate(
        user_email=user.email,
        catalog_item_id=item_id,
        name=template_name,
        description=template_description,
        parameters=parameters,
        default_cost_center=cost_center,
        default_environment_type=environment_type,
        default_project_code=project_code,
        default_expiration_days=expiration_days,
    )

    db.add(tmpl)

    # Log action
    await log_template_saved(
        db=db,
        user_email=user.email,
        user_name=user.name,
        catalog_item_id=item_id,
        template_name=template_name,
        request=request,
    )

    await db.commit()

    return RedirectResponse(url="/templates", status_code=302)


@router.get("/{template_id}")
async def view_template(
    request: Request,
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """View a saved template."""
    user = get_current_user(request)

    result = await db.execute(
        select(RequestTemplate).where(RequestTemplate.id == template_id)
    )
    tmpl = result.scalar_one_or_none()

    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    if tmpl.user_email != user.email:
        raise HTTPException(status_code=403, detail="Not your template")

    item = catalog_service.get_by_id(tmpl.catalog_item_id)

    return templates.TemplateResponse(
        "template_detail.html",
        {
            "request": request,
            "user": user,
            "template": tmpl,
            "catalog_item": item,
        },
    )


@router.get("/{template_id}/use")
async def use_template(
    request: Request,
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Use a template to pre-fill a deployment request form."""
    user = get_current_user(request)

    result = await db.execute(
        select(RequestTemplate).where(RequestTemplate.id == template_id)
    )
    tmpl = result.scalar_one_or_none()

    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    if tmpl.user_email != user.email:
        raise HTTPException(status_code=403, detail="Not your template")

    item = catalog_service.get_by_id(tmpl.catalog_item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Catalog item no longer exists")

    return templates.TemplateResponse(
        "request_form.html",
        {
            "request": request,
            "user": user,
            "item": item,
            "form_data": tmpl.parameters,
            "prefilled_cost_center": tmpl.default_cost_center,
            "prefilled_environment_type": tmpl.default_environment_type,
            "prefilled_project_code": tmpl.default_project_code,
            "prefilled_expiration_days": tmpl.default_expiration_days,
            "from_template": tmpl.name,
        },
    )


@router.delete("/{template_id}")
async def delete_template(
    request: Request,
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved template."""
    user = get_current_user(request)

    result = await db.execute(
        select(RequestTemplate).where(RequestTemplate.id == template_id)
    )
    tmpl = result.scalar_one_or_none()

    if not tmpl:
        return JSONResponse(status_code=404, content={"error": "Template not found"})

    if tmpl.user_email != user.email:
        return JSONResponse(status_code=403, content={"error": "Not your template"})

    await db.delete(tmpl)
    await db.commit()

    return JSONResponse(content={"status": "deleted"})
