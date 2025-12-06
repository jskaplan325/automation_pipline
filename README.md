# Terraform Self-Service Portal

An internal web portal for requesting Azure infrastructure deployments via pre-built Terraform templates. Features a novice-friendly catalog, cost visibility, and approval workflow that triggers Azure DevOps pipelines.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![HTMX](https://img.shields.io/badge/HTMX-1.9-purple.svg)
![License](https://img.shields.io/badge/license-Internal-gray.svg)

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend | Python FastAPI | Async, excellent Azure SDK support, auto-generated API docs |
| Frontend | Jinja2 + HTMX | Server-rendered, minimal JS, fast MVP development |
| Database | SQLite | Zero setup for MVP, easy migration path to Azure SQL |
| Styling | Tailwind CSS (CDN) | Clean UI without heavy build process |

## Features

### Core Features
- **Template Catalog** - Browse available Terraform templates with descriptions aimed at novice users
- **Cost Estimates** - See estimated monthly costs before requesting deployments
- **Request Workflow** - Submit requests, track status, view deployment results
- **Approval System** - Approvers review requests before pipelines run
- **ADO Integration** - Automatically triggers Azure DevOps pipelines on approval
- **Notifications** - Email and Microsoft Teams notifications for request updates

### Quick Wins & Personalization
- **Favorites** - Save templates to favorites for quick access; filter catalog to view only favorites
- **Request Templates** - Save parameter configurations as reusable templates
- **Deployment Tags** - Tag deployments with cost center, environment type, and project code
- **Environment Expiration** - Set expiration dates for temporary deployments

### Operations & Lifecycle
- **Active Deployments** - View and manage your running infrastructure
- **Scale Operations** - Request scaling of deployed resources (with approval)
- **Destroy Operations** - Request destruction of deployments (with approval)
- **Resource Health** - Track health status (healthy, degraded, unhealthy) of deployments
- **Audit Log** - Complete audit trail of all actions for compliance

### Interactive UI (HTMX-powered)
- **Live Search** - Real-time catalog filtering as you type (no page reload)
- **Instant Favorites** - Toggle favorites with immediate visual feedback
- **Inline Approvals** - Approve/reject requests directly from the dashboard
- **Auto-refresh Status** - Deploying requests automatically poll for updates
- **Modal Confirmations** - Destroy confirmations via modal dialogs

## Quick Start

### Prerequisites

- Python 3.9+
- Azure DevOps account with existing Terraform pipelines
- (Optional) SMTP server for email notifications
- (Optional) Microsoft Teams incoming webhook

### Installation

```bash
# Clone the repository
git clone https://github.com/jskaplan325/automation_pipline.git
cd automation_pipline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your configuration (see Configuration section)

# Initialize database with demo data
python seed_demo_data.py

# Run the development server
python run.py
```

Open http://localhost:8000 in your browser.

### Demo Mode

The `seed_demo_data.py` script populates the database with sample requests in various states (pending, approved, deploying, completed, rejected, failed) so you can explore the full workflow.

To switch between user and approver views during testing:
- **User view**: http://localhost:8000/dev/set-role/user
- **Approver view**: http://localhost:8000/dev/set-role/approver

## Configuration

Create a `.env` file based on `.env.example`:

```bash
# Application
SECRET_KEY=your-secret-key-change-in-production
DEBUG=true

# Azure DevOps
ADO_ORG_URL=https://dev.azure.com/your-org
ADO_PAT=your-personal-access-token  # Requires Build Read & Execute scope

# Email (SMTP)
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@company.com
SMTP_PASSWORD=your-password
APPROVER_EMAILS=approver1@company.com,approver2@company.com

# Microsoft Teams (optional)
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # SQLite database setup
│   ├── models.py            # SQLAlchemy models
│   ├── auth.py              # Authentication (placeholder for Entra ID)
│   ├── catalog.py           # Catalog service for loading templates
│   ├── routers/
│   │   ├── catalog.py       # Catalog browsing endpoints
│   │   ├── requests.py      # Deployment request endpoints
│   │   ├── approvals.py     # Approval workflow endpoints
│   │   ├── favorites.py     # Favorites management endpoints
│   │   ├── templates.py     # Request templates endpoints
│   │   ├── operations.py    # Scale/destroy operations endpoints
│   │   └── audit.py         # Audit log endpoints
│   ├── services/
│   │   ├── ado_client.py    # Azure DevOps API integration
│   │   ├── email_service.py # Email notifications
│   │   ├── teams_webhook.py # Teams notifications
│   │   └── audit_service.py # Audit logging service
│   └── templates/
│       ├── *.html           # Full page templates
│       └── partials/        # HTMX partial templates
├── catalog/                 # Terraform template definitions (YAML)
├── static/                  # CSS and static assets
├── requirements.txt
├── run.py                   # Development server runner
└── seed_demo_data.py        # Demo data seeder
```

## Adding New Templates

Create a new YAML file in the `catalog/` directory:

```yaml
id: my-template
name: My New Template
description: |
  Detailed description of what this template deploys.

  **Best for**: Who should use this template
  **Skill level**: Beginner friendly

category: development
skill_level: beginner
estimated_monthly_cost_usd: 50-100

cost_breakdown:
  - component: Resource 1
    estimate: "$25/month"
  - component: Resource 2
    estimate: "$25-75/month"

parameters:
  - name: project_name
    label: Project Name
    type: string
    required: true
    description: A name for your project

  - name: region
    label: Azure Region
    type: select
    options: [eastus, westus2, northeurope]
    default: eastus

ado_pipeline:
  project: YourADOProject
  pipeline_id: 123
  branch: main
```

## Workflow

```
User browses catalog
        │
        ▼
User selects template, fills parameters
        │
        ▼
Request created (status: pending_approval)
        │
        ▼
Email sent to approvers
        │
        ▼
Approver reviews in dashboard
        │
        ├─── Rejected ───▶ Email requester with reason
        │
        ▼
Approved ───▶ Trigger ADO pipeline
        │
        ▼
Pipeline runs Terraform
        │
        ▼
Completed ───▶ Email requester with details
```

## Production Deployment

### Authentication

The current implementation uses mock authentication for development. For production:

1. Register an app in Azure AD / Entra ID
2. Update `app/auth.py` to validate Entra ID tokens
3. See comments in `auth.py` for implementation guidance

### Database

For production, consider migrating from SQLite to:
- Azure SQL Database
- PostgreSQL on Azure

Update `DATABASE_URL` in your `.env` file accordingly.

### Hosting

Recommended Azure hosting options:
- Azure App Service (simplest)
- Azure Container Apps
- Azure Kubernetes Service

## API Documentation

When the server is running, interactive API docs are available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

## License

Internal use only.
