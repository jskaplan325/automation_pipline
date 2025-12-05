#!/usr/bin/env python3
"""
Seed script to populate the database with demo data for demonstrations.

Usage:
    python seed_demo_data.py
"""
import asyncio
from datetime import datetime, timedelta

from app.database import init_db, async_session_maker
from app.models import DeploymentRequest, RequestStatus


DEMO_REQUESTS = [
    # Pending approval requests
    {
        "catalog_item_id": "azure-foundry",
        "requester_email": "alice.johnson@company.com",
        "requester_name": "Alice Johnson",
        "parameters": {
            "project_name": "customer-insights-ai",
            "region": "eastus",
            "enable_gpt4": "true",
            "compute_size": "Standard_DS3_v2",
        },
        "status": RequestStatus.PENDING_APPROVAL,
        "created_at": datetime.utcnow() - timedelta(hours=2),
    },
    {
        "catalog_item_id": "vector-playground",
        "requester_email": "bob.smith@company.com",
        "requester_name": "Bob Smith",
        "parameters": {
            "environment_name": "product-search-poc",
            "region": "eastus",
            "cosmos_throughput": "serverless",
            "mongodb_tier": "M10",
            "enable_notebooks": "true",
        },
        "status": RequestStatus.PENDING_APPROVAL,
        "created_at": datetime.utcnow() - timedelta(hours=5),
    },
    # Approved and deploying
    {
        "catalog_item_id": "dev-environment",
        "requester_email": "carol.davis@company.com",
        "requester_name": "Carol Davis",
        "parameters": {
            "app_name": "inventory-api",
            "region": "westus2",
            "runtime_stack": "dotnet-8",
            "sql_size": "Standard-S0",
        },
        "status": RequestStatus.DEPLOYING,
        "created_at": datetime.utcnow() - timedelta(days=1),
        "approved_by": "approver@company.com",
        "approved_at": datetime.utcnow() - timedelta(hours=1),
        "ado_build_id": 12847,
        "ado_build_url": "https://dev.azure.com/your-org/InfrastructureTeam/_build/results?buildId=12847",
    },
    # Completed successfully
    {
        "catalog_item_id": "azure-foundry",
        "requester_email": "david.wilson@company.com",
        "requester_name": "David Wilson",
        "parameters": {
            "project_name": "fraud-detection-ml",
            "region": "northeurope",
            "enable_gpt4": "true",
            "compute_size": "Standard_NC6s_v3",
        },
        "status": RequestStatus.COMPLETED,
        "created_at": datetime.utcnow() - timedelta(days=3),
        "approved_by": "approver@company.com",
        "approved_at": datetime.utcnow() - timedelta(days=3, hours=-2),
        "ado_build_id": 12801,
        "ado_build_url": "https://dev.azure.com/your-org/InfrastructureTeam/_build/results?buildId=12801",
        "deployment_output": """Terraform Apply Complete!

Resources created:
  - azurerm_resource_group.main
  - azurerm_ai_hub.main
  - azurerm_ai_project.main
  - azurerm_cognitive_account.openai
  - azurerm_storage_account.main
  - azurerm_key_vault.main

Outputs:
  ai_hub_endpoint = "https://fraud-detection-ml.cognitiveservices.azure.com"
  storage_account = "frauddetectionmlstore"

Deployment completed in 8m 32s""",
    },
    {
        "catalog_item_id": "dev-environment",
        "requester_email": "emma.brown@company.com",
        "requester_name": "Emma Brown",
        "parameters": {
            "app_name": "customer-portal",
            "region": "eastus",
            "runtime_stack": "node-20",
            "sql_size": "Basic",
        },
        "status": RequestStatus.COMPLETED,
        "created_at": datetime.utcnow() - timedelta(days=7),
        "approved_by": "approver@company.com",
        "approved_at": datetime.utcnow() - timedelta(days=7, hours=-1),
        "ado_build_id": 12756,
        "ado_build_url": "https://dev.azure.com/your-org/InfrastructureTeam/_build/results?buildId=12756",
        "deployment_output": """Terraform Apply Complete!

Resources created:
  - azurerm_resource_group.main
  - azurerm_service_plan.main
  - azurerm_linux_web_app.main
  - azurerm_mssql_server.main
  - azurerm_mssql_database.main
  - azurerm_storage_account.main
  - azurerm_application_insights.main
  - azurerm_key_vault.main

Outputs:
  app_url = "https://customer-portal.azurewebsites.net"
  sql_server = "customer-portal-sql.database.windows.net"

Deployment completed in 5m 18s""",
    },
    # Rejected request
    {
        "catalog_item_id": "vector-playground",
        "requester_email": "frank.miller@company.com",
        "requester_name": "Frank Miller",
        "parameters": {
            "environment_name": "experimental-vectors",
            "region": "westus2",
            "cosmos_throughput": "1000-ru",
            "mongodb_tier": "M30",
            "enable_notebooks": "true",
        },
        "status": RequestStatus.REJECTED,
        "created_at": datetime.utcnow() - timedelta(days=2),
        "approved_by": "approver@company.com",
        "approved_at": datetime.utcnow() - timedelta(days=2, hours=-3),
        "rejection_reason": "Budget not approved for M30 tier. Please resubmit with M10 tier for initial POC, we can scale up later if the project proves successful.",
    },
    # Failed deployment
    {
        "catalog_item_id": "azure-foundry",
        "requester_email": "grace.lee@company.com",
        "requester_name": "Grace Lee",
        "parameters": {
            "project_name": "sentiment-analysis",
            "region": "westeurope",
            "enable_gpt4": "true",
            "compute_size": "Standard_DS4_v2",
        },
        "status": RequestStatus.FAILED,
        "created_at": datetime.utcnow() - timedelta(days=1, hours=12),
        "approved_by": "approver@company.com",
        "approved_at": datetime.utcnow() - timedelta(days=1, hours=10),
        "ado_build_id": 12832,
        "ado_build_url": "https://dev.azure.com/your-org/InfrastructureTeam/_build/results?buildId=12832",
        "deployment_output": """Error: creating AI Services Account

Error: insufficient quota for GPT-4 in westeurope region.
Current quota: 0 TPM, Requested: 10000 TPM

Please request quota increase or select a different region.

Deployment failed after 2m 45s""",
    },
]


async def seed_database():
    """Seed the database with demo data."""
    print("Initializing database...")
    await init_db()

    async with async_session_maker() as session:
        # Check if we already have data
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count()).select_from(DeploymentRequest)
        )
        count = result.scalar()

        if count > 0:
            print(f"Database already has {count} requests. Clearing existing data...")
            await session.execute(
                DeploymentRequest.__table__.delete()
            )
            await session.commit()

        print("Creating demo requests...")
        for data in DEMO_REQUESTS:
            request = DeploymentRequest(**data)
            session.add(request)
            print(f"  + {data['requester_name']}: {data['catalog_item_id']} ({data['status'].value})")

        await session.commit()
        print(f"\nSeeded {len(DEMO_REQUESTS)} demo requests!")
        print("\nYou can now run the app with: python run.py")
        print("Then open http://localhost:8000")
        print("\nTip: Use /dev/set-role/approver to switch to approver view")


if __name__ == "__main__":
    asyncio.run(seed_database())
