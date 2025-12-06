"""
Catalog service for loading and managing Terraform template definitions.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class CostBreakdown:
    """Individual cost component."""
    component: str
    estimate: str


@dataclass
class Parameter:
    """A parameter that users must provide when requesting a deployment."""
    name: str
    label: str
    type: str  # string, number, select, boolean
    description: str = ""
    required: bool = True
    default: Optional[str] = None
    options: list[str] = field(default_factory=list)  # For select type
    min_value: Optional[int] = None  # For number type
    max_value: Optional[int] = None  # For number type


@dataclass
class ADOPipeline:
    """Azure DevOps pipeline reference."""
    project: str
    pipeline_id: int
    branch: str = "main"
    module_name: Optional[str] = None  # For generic pipeline: terraform/<module_name>/


@dataclass
class CatalogItem:
    """A Terraform template available in the catalog."""
    id: str
    name: str
    description: str
    category: str
    estimated_monthly_cost_usd: str  # e.g., "150-300" or "~50"
    cost_breakdown: list[CostBreakdown]
    parameters: list[Parameter]
    ado_pipeline: ADOPipeline
    icon: str = "cloud"  # Icon name for UI
    skill_level: str = "beginner"  # beginner, intermediate, advanced
    tags: list[str] = field(default_factory=list)

    @property
    def description_short(self) -> str:
        """Get first paragraph of description for card preview."""
        lines = self.description.strip().split("\n\n")
        return lines[0] if lines else self.description[:200]


class CatalogService:
    """Service for loading and querying the catalog."""

    def __init__(self, catalog_dir: str = "catalog"):
        self.catalog_dir = Path(catalog_dir)
        self._items: dict[str, CatalogItem] = {}
        self._loaded = False

    def _load_catalog(self) -> None:
        """Load all catalog items from YAML files."""
        if self._loaded:
            return

        self._items = {}

        if not self.catalog_dir.exists():
            return

        for yaml_file in self.catalog_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)

                if not data:
                    continue

                # Parse cost breakdown
                cost_breakdown = [
                    CostBreakdown(**cb)
                    for cb in data.get("cost_breakdown", [])
                ]

                # Parse parameters
                parameters = [
                    Parameter(
                        name=p["name"],
                        label=p.get("label", p["name"]),
                        type=p.get("type", "string"),
                        description=p.get("description", ""),
                        required=p.get("required", True),
                        default=p.get("default"),
                        options=p.get("options", []),
                        min_value=p.get("min_value"),
                        max_value=p.get("max_value"),
                    )
                    for p in data.get("parameters", [])
                ]

                # Parse ADO pipeline
                ado_data = data.get("ado_pipeline", {})
                ado_pipeline = ADOPipeline(
                    project=ado_data.get("project", ""),
                    pipeline_id=ado_data.get("pipeline_id", 0),
                    branch=ado_data.get("branch", "main"),
                    module_name=ado_data.get("module_name"),
                )

                item = CatalogItem(
                    id=data["id"],
                    name=data["name"],
                    description=data.get("description", ""),
                    category=data.get("category", "general"),
                    estimated_monthly_cost_usd=str(data.get("estimated_monthly_cost_usd", "Unknown")),
                    cost_breakdown=cost_breakdown,
                    parameters=parameters,
                    ado_pipeline=ado_pipeline,
                    icon=data.get("icon", "cloud"),
                    skill_level=data.get("skill_level", "beginner"),
                    tags=data.get("tags", []),
                )

                self._items[item.id] = item

            except Exception as e:
                print(f"Error loading catalog item from {yaml_file}: {e}")

        self._loaded = True

    def reload(self) -> None:
        """Force reload of catalog from disk."""
        self._loaded = False
        self._load_catalog()

    def get_all(self) -> list[CatalogItem]:
        """Get all catalog items."""
        self._load_catalog()
        return list(self._items.values())

    def get_by_id(self, item_id: str) -> Optional[CatalogItem]:
        """Get a specific catalog item by ID."""
        self._load_catalog()
        return self._items.get(item_id)

    def get_by_category(self, category: str) -> list[CatalogItem]:
        """Get all catalog items in a category."""
        self._load_catalog()
        return [item for item in self._items.values() if item.category == category]

    def get_categories(self) -> list[str]:
        """Get all unique categories."""
        self._load_catalog()
        return sorted(set(item.category for item in self._items.values()))

    def search(self, query: str) -> list[CatalogItem]:
        """Search catalog items by name, description, or tags."""
        self._load_catalog()
        query_lower = query.lower()
        results = []

        for item in self._items.values():
            if (
                query_lower in item.name.lower()
                or query_lower in item.description.lower()
                or any(query_lower in tag.lower() for tag in item.tags)
            ):
                results.append(item)

        return results


# Global catalog service instance
catalog_service = CatalogService()
