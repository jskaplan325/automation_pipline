"""
SQLAlchemy database models.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, JSON
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


class ReminderType(PyEnum):
    """Type of approval reminder sent."""
    EMAIL = "email"
    TEAMS = "teams"


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class DeploymentRequest(Base):
    """A request to deploy a Terraform template."""

    __tablename__ = "deployment_requests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    catalog_item_id: Mapped[str] = mapped_column(String(100), index=True)
    requester_email: Mapped[str] = mapped_column(String(255))
    requester_name: Mapped[str] = mapped_column(String(255))
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)

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

    # Relationships
    reminders: Mapped[list["ApprovalReminder"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DeploymentRequest {self.id} ({self.catalog_item_id})>"


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
