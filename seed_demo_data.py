#!/usr/bin/env python3
"""
Seed script to populate the database with demo data for demonstrations.

Usage:
    python seed_demo_data.py
"""
import asyncio
from datetime import datetime, timedelta

from app.database import init_db, async_session_maker
from app.models import (
    DeploymentRequest, RequestStatus, RequestType, ResourceHealth,
    Favorite, RequestTemplate, AuditLog, AuditAction
)


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
        "request_type": RequestType.DEPLOY,
        "environment_type": "development",
        "cost_center": "CC-AI-001",
        "project_code": "CUST-INSIGHTS",
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
        "request_type": RequestType.DEPLOY,
        "environment_type": "testing",
        "cost_center": "CC-SEARCH-002",
        "expires_at": datetime.utcnow() + timedelta(days=30),
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
            "size": "medium",
        },
        "status": RequestStatus.DEPLOYING,
        "request_type": RequestType.DEPLOY,
        "environment_type": "staging",
        "cost_center": "CC-INV-003",
        "project_code": "INV-API",
        "created_at": datetime.utcnow() - timedelta(days=1),
        "approved_by": "approver@company.com",
        "approved_at": datetime.utcnow() - timedelta(hours=1),
        "ado_build_id": 12847,
        "ado_build_url": "https://dev.azure.com/your-org/InfrastructureTeam/_build/results?buildId=12847",
    },
    # Completed successfully - Active Deployments
    {
        "catalog_item_id": "azure-foundry",
        "requester_email": "david.wilson@company.com",
        "requester_name": "David Wilson",
        "parameters": {
            "project_name": "fraud-detection-ml",
            "region": "northeurope",
            "enable_gpt4": "true",
            "compute_size": "Standard_NC6s_v3",
            "size": "large",
        },
        "status": RequestStatus.COMPLETED,
        "request_type": RequestType.DEPLOY,
        "environment_type": "production",
        "cost_center": "CC-FRAUD-001",
        "project_code": "FRAUD-DET",
        "resource_health": ResourceHealth.HEALTHY,
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
            "size": "small",
        },
        "status": RequestStatus.COMPLETED,
        "request_type": RequestType.DEPLOY,
        "environment_type": "development",
        "cost_center": "CC-PORTAL-001",
        "project_code": "CUST-PORTAL",
        "resource_health": ResourceHealth.HEALTHY,
        "expires_at": datetime.utcnow() + timedelta(days=23),
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
    # Another active deployment - degraded health
    {
        "catalog_item_id": "aks-cluster",
        "requester_email": "test@company.com",
        "requester_name": "Test User",
        "parameters": {
            "cluster_name": "shared-services-aks",
            "region": "eastus",
            "node_count": "3",
            "node_size": "Standard_D4s_v3",
            "size": "medium",
        },
        "status": RequestStatus.COMPLETED,
        "request_type": RequestType.DEPLOY,
        "environment_type": "production",
        "cost_center": "CC-INFRA-001",
        "project_code": "SHARED-SVC",
        "resource_health": ResourceHealth.DEGRADED,
        "created_at": datetime.utcnow() - timedelta(days=14),
        "approved_by": "approver@company.com",
        "approved_at": datetime.utcnow() - timedelta(days=14, hours=-1),
        "ado_build_id": 12650,
        "deployment_output": """Terraform Apply Complete!

Resources created:
  - azurerm_resource_group.main
  - azurerm_kubernetes_cluster.main
  - azurerm_container_registry.main

Outputs:
  cluster_fqdn = "shared-services-aks.eastus.azmk8s.io"
  acr_login_server = "sharedservicesacr.azurecr.io"

Deployment completed in 12m 45s""",
    },
    # Active deployment expiring soon
    {
        "catalog_item_id": "serverless-api",
        "requester_email": "test@company.com",
        "requester_name": "Test User",
        "parameters": {
            "function_name": "webhook-processor",
            "region": "eastus",
            "runtime": "python-3.11",
            "size": "small",
        },
        "status": RequestStatus.COMPLETED,
        "request_type": RequestType.DEPLOY,
        "environment_type": "testing",
        "cost_center": "CC-TEST-001",
        "resource_health": ResourceHealth.HEALTHY,
        "expires_at": datetime.utcnow() + timedelta(days=5),
        "created_at": datetime.utcnow() - timedelta(days=25),
        "approved_by": "approver@company.com",
        "approved_at": datetime.utcnow() - timedelta(days=25, hours=-1),
        "ado_build_id": 12500,
        "deployment_output": """Terraform Apply Complete!

Resources created:
  - azurerm_resource_group.main
  - azurerm_storage_account.main
  - azurerm_service_plan.main
  - azurerm_linux_function_app.main
  - azurerm_application_insights.main

Outputs:
  function_url = "https://webhook-processor.azurewebsites.net"

Deployment completed in 3m 22s""",
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
        "request_type": RequestType.DEPLOY,
        "environment_type": "development",
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
        "request_type": RequestType.DEPLOY,
        "environment_type": "development",
        "cost_center": "CC-SENT-001",
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
    # Scale request pending
    {
        "catalog_item_id": "aks-cluster",
        "requester_email": "david.wilson@company.com",
        "requester_name": "David Wilson",
        "parameters": {
            "cluster_name": "fraud-detection-ml",
        },
        "status": RequestStatus.PENDING_APPROVAL,
        "request_type": RequestType.SCALE,
        "environment_type": "production",
        "cost_center": "CC-FRAUD-001",
        "previous_size": "medium",
        "new_size": "large",
        "created_at": datetime.utcnow() - timedelta(hours=1),
    },
]


DEMO_FAVORITES = [
    {"user_email": "test@company.com", "catalog_item_id": "azure-foundry"},
    {"user_email": "test@company.com", "catalog_item_id": "aks-cluster"},
    {"user_email": "test@company.com", "catalog_item_id": "serverless-api"},
    {"user_email": "alice.johnson@company.com", "catalog_item_id": "azure-foundry"},
    {"user_email": "alice.johnson@company.com", "catalog_item_id": "ml-workspace"},
]


DEMO_TEMPLATES = [
    {
        "user_email": "test@company.com",
        "catalog_item_id": "dev-environment",
        "name": "Standard Dev Setup",
        "description": "My standard development environment configuration",
        "parameters": {
            "region": "eastus",
            "runtime_stack": "node-20",
            "sql_size": "Basic",
            "size": "small",
        },
        "default_environment_type": "development",
        "default_cost_center": "CC-DEV-001",
    },
    {
        "user_email": "test@company.com",
        "catalog_item_id": "azure-foundry",
        "name": "AI Project Template",
        "description": "Pre-configured AI Foundry for data science projects",
        "parameters": {
            "region": "eastus",
            "enable_gpt4": "true",
            "compute_size": "Standard_DS3_v2",
            "size": "medium",
        },
        "default_environment_type": "development",
        "default_cost_center": "CC-AI-001",
        "default_expiration_days": 90,
    },
    {
        "user_email": "alice.johnson@company.com",
        "catalog_item_id": "serverless-api",
        "name": "Quick API Setup",
        "description": "Serverless API for quick prototypes",
        "parameters": {
            "region": "eastus",
            "runtime": "python-3.11",
            "size": "small",
        },
        "default_environment_type": "testing",
        "default_expiration_days": 30,
    },
]


def generate_audit_logs(requests_map):
    """Generate audit log entries based on demo requests."""
    logs = []

    for req_data in DEMO_REQUESTS:
        request_id = requests_map.get(req_data['requester_email'] + req_data['catalog_item_id'])
        if not request_id:
            continue

        # Request created
        logs.append({
            "user_email": req_data['requester_email'],
            "user_name": req_data['requester_name'],
            "action": AuditAction.REQUEST_CREATED,
            "request_id": request_id,
            "catalog_item_id": req_data['catalog_item_id'],
            "details": {"request_type": req_data.get('request_type', RequestType.DEPLOY).value},
            "timestamp": req_data['created_at'],
        })

        # Approvals/rejections
        if req_data.get('approved_by'):
            if req_data['status'] == RequestStatus.REJECTED:
                logs.append({
                    "user_email": req_data['approved_by'],
                    "user_name": "System Approver",
                    "action": AuditAction.REQUEST_REJECTED,
                    "request_id": request_id,
                    "catalog_item_id": req_data['catalog_item_id'],
                    "details": {"reason": req_data.get('rejection_reason', '')[:100]},
                    "timestamp": req_data['approved_at'],
                })
            else:
                logs.append({
                    "user_email": req_data['approved_by'],
                    "user_name": "System Approver",
                    "action": AuditAction.REQUEST_APPROVED,
                    "request_id": request_id,
                    "catalog_item_id": req_data['catalog_item_id'],
                    "timestamp": req_data['approved_at'],
                })

        # Deployment completed/failed
        if req_data['status'] == RequestStatus.COMPLETED:
            logs.append({
                "user_email": "system@terraform-portal.local",
                "user_name": "System",
                "action": AuditAction.DEPLOYMENT_COMPLETED,
                "request_id": request_id,
                "catalog_item_id": req_data['catalog_item_id'],
                "timestamp": req_data['approved_at'] + timedelta(minutes=10) if req_data.get('approved_at') else req_data['created_at'],
            })
        elif req_data['status'] == RequestStatus.FAILED:
            logs.append({
                "user_email": "system@terraform-portal.local",
                "user_name": "System",
                "action": AuditAction.DEPLOYMENT_FAILED,
                "request_id": request_id,
                "catalog_item_id": req_data['catalog_item_id'],
                "details": {"error": "See deployment output for details"},
                "timestamp": req_data['approved_at'] + timedelta(minutes=5) if req_data.get('approved_at') else req_data['created_at'],
            })

    # Add some favorite actions
    logs.append({
        "user_email": "test@company.com",
        "user_name": "Test User",
        "action": AuditAction.FAVORITE_ADDED,
        "catalog_item_id": "azure-foundry",
        "timestamp": datetime.utcnow() - timedelta(days=5),
    })
    logs.append({
        "user_email": "test@company.com",
        "user_name": "Test User",
        "action": AuditAction.TEMPLATE_SAVED,
        "catalog_item_id": "dev-environment",
        "details": {"template_name": "Standard Dev Setup"},
        "timestamp": datetime.utcnow() - timedelta(days=4),
    })

    return logs


async def seed_database():
    """Seed the database with demo data."""
    print("Initializing database...")
    await init_db()

    async with async_session_maker() as session:
        # Check if we already have data and clear it
        from sqlalchemy import select, func

        result = await session.execute(
            select(func.count()).select_from(DeploymentRequest)
        )
        count = result.scalar()

        if count > 0:
            print(f"Database already has {count} requests. Clearing existing data...")
            # Clear all tables
            await session.execute(AuditLog.__table__.delete())
            await session.execute(RequestTemplate.__table__.delete())
            await session.execute(Favorite.__table__.delete())
            await session.execute(DeploymentRequest.__table__.delete())
            await session.commit()

        print("Creating demo requests...")
        requests_map = {}
        for data in DEMO_REQUESTS:
            request = DeploymentRequest(**data)
            session.add(request)
            await session.flush()
            requests_map[data['requester_email'] + data['catalog_item_id']] = request.id
            print(f"  + {data['requester_name']}: {data['catalog_item_id']} ({data['status'].value})")

        print("\nCreating demo favorites...")
        for data in DEMO_FAVORITES:
            favorite = Favorite(**data)
            session.add(favorite)
            print(f"  + {data['user_email']}: {data['catalog_item_id']}")

        print("\nCreating demo templates...")
        for data in DEMO_TEMPLATES:
            template = RequestTemplate(**data)
            session.add(template)
            print(f"  + {data['user_email']}: {data['name']}")

        print("\nCreating audit log entries...")
        audit_logs = generate_audit_logs(requests_map)
        for data in audit_logs:
            log = AuditLog(**data)
            session.add(log)
        print(f"  + {len(audit_logs)} audit entries created")

        await session.commit()

        print(f"\n{'='*50}")
        print(f"Seeded demo data:")
        print(f"  - {len(DEMO_REQUESTS)} deployment requests")
        print(f"  - {len(DEMO_FAVORITES)} favorites")
        print(f"  - {len(DEMO_TEMPLATES)} saved templates")
        print(f"  - {len(audit_logs)} audit log entries")
        print(f"{'='*50}")
        print("\nYou can now run the app with: python run.py")
        print("Then open http://localhost:8000")
        print("\nTip: Use /dev/set-role/approver to switch to approver view")
        print("New features to try:")
        print("  - /operations/active - View active deployments (scale/destroy)")
        print("  - /templates - View saved request templates")
        print("  - /audit - View audit log (approver only)")


if __name__ == "__main__":
    asyncio.run(seed_database())
