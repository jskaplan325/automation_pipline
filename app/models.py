"""
SQLAlchemy database models.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RequestStatus(PyEnum):
    """Status of a deployment request."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    SCALING = "scaling"


class RequestType(PyEnum):
    """Type of request."""
    DEPLOY = "deploy"
    DESTROY = "destroy"
    SCALE = "scale"


class ResourceHealth(PyEnum):
    """Health status of deployed resources."""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ReminderType(PyEnum):
    """Type of approval reminder sent."""
    EMAIL = "email"
    TEAMS = "teams"


class AuditAction(PyEnum):
    """Types of auditable actions."""
    REQUEST_CREATED = "request_created"
    REQUEST_APPROVED = "request_approved"
    REQUEST_REJECTED = "request_rejected"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"
    DESTROY_REQUESTED = "destroy_requested"
    DESTROY_COMPLETED = "destroy_completed"
    SCALE_REQUESTED = "scale_requested"
    SCALE_COMPLETED = "scale_completed"
    FAVORITE_ADDED = "favorite_added"
    FAVORITE_REMOVED = "favorite_removed"
    TEMPLATE_SAVED = "template_saved"


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class DeploymentRequest(Base):
    """A request to deploy, destroy, or scale a Terraform template."""

    __tablename__ = "deployment_requests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    catalog_item_id: Mapped[str] = mapped_column(String(100), index=True)
    requester_email: Mapped[str] = mapped_column(String(255))
    requester_name: Mapped[str] = mapped_column(String(255))
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)

    # Request type (deploy, destroy, scale)
    request_type: Mapped[RequestType] = mapped_column(
        Enum(RequestType), default=RequestType.DEPLOY
    )

    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus), default=RequestStatus.PENDING_APPROVAL
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Approval fields
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ADO integration fields
    ado_build_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    ado_build_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Deployment result
    deployment_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Deployment tags for cost tracking
    cost_center: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    environment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # dev, staging, prod
    project_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Expiration for auto-destroy
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expiration_warning_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Resource health tracking
    resource_health: Mapped[ResourceHealth] = mapped_column(
        Enum(ResourceHealth), default=ResourceHealth.UNKNOWN
    )
    health_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    health_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # For scale requests - link to original deployment
    parent_request_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("deployment_requests.id"), nullable=True
    )
    previous_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    reminders: Mapped[list["ApprovalReminder"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DeploymentRequest {self.id} ({self.catalog_item_id})>"

    @property
    def is_active(self) -> bool:
        """Check if deployment is currently active."""
        return self.status in [RequestStatus.COMPLETED, RequestStatus.DEPLOYING]

    @property
    def can_destroy(self) -> bool:
        """Check if deployment can be destroyed."""
        return self.status == RequestStatus.COMPLETED and self.request_type == RequestType.DEPLOY

    @property
    def can_scale(self) -> bool:
        """Check if deployment can be scaled."""
        return self.status == RequestStatus.COMPLETED and self.request_type == RequestType.DEPLOY


class ApprovalReminder(Base):
    """Track reminders sent for pending approvals."""

    __tablename__ = "approval_reminders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    request_id: Mapped[str] = mapped_column(
        ForeignKey("deployment_requests.id"), index=True
    )
    reminder_type: Mapped[ReminderType] = mapped_column(Enum(ReminderType))
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    request: Mapped["DeploymentRequest"] = relationship(back_populates="reminders")

    def __repr__(self) -> str:
        return f"<ApprovalReminder {self.id} ({self.reminder_type.value})>"


class Favorite(Base):
    """User's favorite catalog items for quick access."""

    __tablename__ = "favorites"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    user_email: Mapped[str] = mapped_column(String(255), index=True)
    catalog_item_id: Mapped[str] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Favorite {self.user_email} -> {self.catalog_item_id}>"


class RequestTemplate(Base):
    """Saved request templates for repeat deployments."""

    __tablename__ = "request_templates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    user_email: Mapped[str] = mapped_column(String(255), index=True)
    catalog_item_id: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)

    # Default tags for this template
    default_cost_center: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    default_environment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    default_project_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    default_expiration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<RequestTemplate {self.name} ({self.catalog_item_id})>"


class AuditLog(Base):
    """Audit log for tracking all actions in the system."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    user_email: Mapped[str] = mapped_column(String(255), index=True)
    user_name: Mapped[str] = mapped_column(String(255))
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), index=True)

    # Related entities
    request_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    catalog_item_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Additional details as JSON
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # IP and user agent for security
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.timestamp} {self.action.value} by {self.user_email}>"
