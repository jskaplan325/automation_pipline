"""
Email notification service.
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings


async def send_email(
    to: list[str],
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
) -> bool:
    """
    Send an email using SMTP.

    Args:
        to: List of recipient email addresses
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body (optional, derived from HTML if not provided)

    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.smtp_user or not settings.smtp_password:
        print("Email not configured - skipping send")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = ", ".join(to)

    # Add plain text version
    if body_text:
        msg.attach(MIMEText(body_text, "plain"))

    # Add HTML version
    msg.attach(MIMEText(body_html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_server,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


async def send_approval_request_email(
    request_id: str,
    requester_name: str,
    requester_email: str,
    template_name: str,
    estimated_cost: str,
    parameters: dict,
) -> bool:
    """
    Send email to approvers about a new deployment request.
    """
    subject = f"[Terraform Portal] Approval Required: {template_name}"

    params_html = "".join(
        f"<li><strong>{k}:</strong> {v}</li>"
        for k, v in parameters.items()
    )

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2563eb;">New Deployment Request</h2>

        <p>A new deployment request requires your approval:</p>

        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Template:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{template_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Requested by:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{requester_name} ({requester_email})</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Est. Monthly Cost:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: #dc2626;">${estimated_cost}</td>
            </tr>
        </table>

        <h3>Parameters:</h3>
        <ul>
            {params_html}
        </ul>

        <p>
            <a href="http://localhost:8000/approvals/{request_id}"
               style="display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px;">
                Review Request
            </a>
        </p>

        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            This is an automated message from Terraform Portal.
        </p>
    </body>
    </html>
    """

    return await send_email(
        to=settings.approver_email_list,
        subject=subject,
        body_html=body_html,
    )


async def send_approval_notification(
    requester_email: str,
    template_name: str,
    request_id: str,
    approved_by: str,
) -> bool:
    """
    Send email to requester when their request is approved.
    """
    subject = f"[Terraform Portal] Request Approved: {template_name}"

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #16a34a;">Your Request Has Been Approved!</h2>

        <p>Good news! Your deployment request for <strong>{template_name}</strong> has been approved by {approved_by}.</p>

        <p>The deployment is now being processed. You can track the progress:</p>

        <p>
            <a href="http://localhost:8000/requests/{request_id}"
               style="display: inline-block; padding: 12px 24px; background-color: #16a34a; color: white; text-decoration: none; border-radius: 6px;">
                View Status
            </a>
        </p>

        <p>You will receive another notification when the deployment completes.</p>

        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            This is an automated message from Terraform Portal.
        </p>
    </body>
    </html>
    """

    return await send_email(
        to=[requester_email],
        subject=subject,
        body_html=body_html,
    )


async def send_rejection_notification(
    requester_email: str,
    template_name: str,
    request_id: str,
    rejected_by: str,
    reason: str,
) -> bool:
    """
    Send email to requester when their request is rejected.
    """
    subject = f"[Terraform Portal] Request Rejected: {template_name}"

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #dc2626;">Your Request Has Been Rejected</h2>

        <p>Unfortunately, your deployment request for <strong>{template_name}</strong> has been rejected by {rejected_by}.</p>

        <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
            <strong>Reason:</strong><br>
            {reason}
        </div>

        <p>If you have questions about this decision, please contact the approver directly.</p>

        <p>
            <a href="http://localhost:8000/requests/{request_id}"
               style="display: inline-block; padding: 12px 24px; background-color: #6b7280; color: white; text-decoration: none; border-radius: 6px;">
                View Details
            </a>
        </p>

        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            This is an automated message from Terraform Portal.
        </p>
    </body>
    </html>
    """

    return await send_email(
        to=[requester_email],
        subject=subject,
        body_html=body_html,
    )


async def send_deployment_complete_notification(
    requester_email: str,
    template_name: str,
    request_id: str,
    success: bool,
    details: Optional[str] = None,
) -> bool:
    """
    Send email to requester when deployment completes.
    """
    if success:
        subject = f"[Terraform Portal] Deployment Complete: {template_name}"
        color = "#16a34a"
        title = "Deployment Successful!"
        message = "Your infrastructure has been deployed successfully."
    else:
        subject = f"[Terraform Portal] Deployment Failed: {template_name}"
        color = "#dc2626"
        title = "Deployment Failed"
        message = "Unfortunately, there was an error deploying your infrastructure."

    details_html = ""
    if details:
        details_html = f"""
        <div style="background-color: #f3f4f6; padding: 15px; margin: 20px 0; border-radius: 6px;">
            <pre style="margin: 0; white-space: pre-wrap;">{details}</pre>
        </div>
        """

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: {color};">{title}</h2>

        <p>{message}</p>

        {details_html}

        <p>
            <a href="http://localhost:8000/requests/{request_id}"
               style="display: inline-block; padding: 12px 24px; background-color: {color}; color: white; text-decoration: none; border-radius: 6px;">
                View Details
            </a>
        </p>

        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            This is an automated message from Terraform Portal.
        </p>
    </body>
    </html>
    """

    return await send_email(
        to=[requester_email],
        subject=subject,
        body_html=body_html,
    )
