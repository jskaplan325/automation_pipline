"""
Application configuration.

All settings are loaded from environment variables or .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Terraform Portal"
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./terraform_portal.db"

    # Azure DevOps
    ado_org_url: str = "https://dev.azure.com/your-org"
    ado_pat: str = ""  # Personal Access Token - required for ADO integration

    # Email (SMTP)
    smtp_server: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "terraform-portal@company.com"

    # Approvers - comma-separated list of email addresses
    approver_emails: str = "approver@company.com"

    # Teams Webhook (optional)
    teams_webhook_url: Optional[str] = None

    # Approval settings
    approval_reminder_hours: int = 4  # Hours before sending Teams reminder

    @property
    def approver_email_list(self) -> list[str]:
        """Parse approver emails into a list."""
        return [e.strip() for e in self.approver_emails.split(",") if e.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
