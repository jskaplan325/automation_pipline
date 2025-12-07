"""
Admin routes for viewing and auditing Terraform code.
"""
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from app.auth import get_current_user
from app.catalog import catalog_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Base path for terraform modules
TERRAFORM_DIR = Path("terraform")


def get_terraform_files(module_name: str) -> dict[str, str]:
    """
    Get all Terraform files for a module.

    Returns a dict of {filename: content} for all .tf files.
    """
    module_path = TERRAFORM_DIR / module_name
    files = {}

    if not module_path.exists():
        return files

    for tf_file in sorted(module_path.glob("*.tf")):
        try:
            files[tf_file.name] = tf_file.read_text()
        except Exception as e:
            files[tf_file.name] = f"# Error reading file: {e}"

    return files


@router.get("/")
async def admin_dashboard(request: Request):
    """Admin dashboard showing all catalog items with code access."""
    user = get_current_user(request)

    if not user.is_approver:
        raise HTTPException(status_code=403, detail="Admin access required")

    items = catalog_service.get_all()

    # Enrich with terraform module info
    enriched_items = []
    for item in items:
        module_name = item.ado_pipeline.module_name or item.id
        module_path = TERRAFORM_DIR / module_name
        has_terraform = module_path.exists()

        enriched_items.append({
            "item": item,
            "module_name": module_name,
            "has_terraform": has_terraform,
        })

    return templates.TemplateResponse(
        "admin_catalog.html",
        {
            "request": request,
            "user": user,
            "items": enriched_items,
        },
    )


@router.get("/code/{item_id}")
async def view_code(request: Request, item_id: str):
    """View Terraform code for a catalog item."""
    user = get_current_user(request)

    if not user.is_approver:
        raise HTTPException(status_code=403, detail="Admin access required")

    item = catalog_service.get_by_id(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Catalog item not found")

    # Get module name from ado_pipeline or fallback to item id
    module_name = item.ado_pipeline.module_name or item.id
    terraform_files = get_terraform_files(module_name)

    # Also get the catalog YAML
    catalog_path = Path("catalog") / f"{item_id}.yaml"
    catalog_yaml = ""
    if catalog_path.exists():
        try:
            catalog_yaml = catalog_path.read_text()
        except Exception as e:
            catalog_yaml = f"# Error reading file: {e}"

    return templates.TemplateResponse(
        "admin_code_view.html",
        {
            "request": request,
            "user": user,
            "item": item,
            "module_name": module_name,
            "terraform_files": terraform_files,
            "catalog_yaml": catalog_yaml,
            "has_terraform": bool(terraform_files),
        },
    )


@router.get("/api/code/{item_id}")
async def get_code_api(request: Request, item_id: str):
    """API endpoint to get Terraform code as JSON."""
    user = get_current_user(request)

    if not user.is_approver:
        return JSONResponse(status_code=403, content={"error": "Admin access required"})

    item = catalog_service.get_by_id(item_id)

    if not item:
        return JSONResponse(status_code=404, content={"error": "Catalog item not found"})

    module_name = item.ado_pipeline.module_name or item.id
    terraform_files = get_terraform_files(module_name)

    return JSONResponse(content={
        "item_id": item_id,
        "item_name": item.name,
        "module_name": module_name,
        "files": terraform_files,
    })
