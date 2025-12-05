"""
Microsoft Teams webhook integration for notifications.
"""
import httpx
from typing import Optional

from app.config import settings


async def send_teams_message(
    title: str,
    message: str,
    color: str = "0078D4",  # Microsoft blue
    facts: Optional[list[dict]] = None,
    action_url: Optional[str] = None,
    action_text: str = "View Details",
) -> bool:
    """
    Send a message to Microsoft Teams via incoming webhook.

    Args:
        title: Card title
        message: Main message text
        color: Theme color (hex without #)
        facts: List of {"name": "...", "value": "..."} pairs
        action_url: Optional button URL
        action_text: Button text

    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.teams_webhook_url:
        print("Teams webhook not configured - skipping send")
        return False

    # Build adaptive card payload
    # Using MessageCard format for broader compatibility
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": title,
        "sections": [
            {
                "activityTitle": title,
                "text": message,
            }
        ],
    }

    # Add facts if provided
    if facts:
        payload["sections"][0]["facts"] = facts

    # Add action button if provided
    if action_url:
        payload["potentialAction"] = [
            {
                "@type": "OpenUri",
                "name": action_text,
                "targets": [
                    {"os": "default", "uri": action_url}
                ],
            }
        ]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.teams_webhook_url,
                json=payload,
                timeout=30.0,
            )
            # Teams returns 200 with "1" on success
            return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Teams message: {e}")
        return False


async def send_approval_reminder(
    request_id: str,
    requester_name: str,
    template_name: str,
    estimated_cost: str,
    hours_pending: int,
) -> bool:
    """
    Send a reminder to Teams about a pending approval.
    """
    return await send_teams_message(
        title="Pending Approval Reminder",
        message=f"A deployment request has been waiting for approval for {hours_pending} hours.",
        color="FFA500",  # Orange
        facts=[
            {"name": "Template", "value": template_name},
            {"name": "Requested By", "value": requester_name},
            {"name": "Est. Monthly Cost", "value": f"${estimated_cost}"},
            {"name": "Waiting", "value": f"{hours_pending} hours"},
        ],
        action_url=f"http://localhost:8000/approvals/{request_id}",
        action_text="Review Request",
    )


async def send_deployment_notification(
    request_id: str,
    requester_name: str,
    template_name: str,
    status: str,  # "started", "completed", "failed"
    approved_by: Optional[str] = None,
) -> bool:
    """
    Send deployment status notification to Teams.
    """
    if status == "started":
        title = "Deployment Started"
        color = "7B68EE"  # Purple
        message = f"Deployment of {template_name} has started."
    elif status == "completed":
        title = "Deployment Completed"
        color = "28A745"  # Green
        message = f"Deployment of {template_name} completed successfully!"
    else:  # failed
        title = "Deployment Failed"
        color = "DC3545"  # Red
        message = f"Deployment of {template_name} has failed. Please investigate."

    facts = [
        {"name": "Template", "value": template_name},
        {"name": "Requested By", "value": requester_name},
    ]

    if approved_by:
        facts.append({"name": "Approved By", "value": approved_by})

    return await send_teams_message(
        title=title,
        message=message,
        color=color,
        facts=facts,
        action_url=f"http://localhost:8000/requests/{request_id}",
        action_text="View Details",
    )
