"""
Authentication module.

MVP: No authentication - returns mock user for testing.
Production: Integrate with Azure AD / Entra ID.

TODO: Implement Azure AD / Entra ID authentication
See: https://learn.microsoft.com/en-us/azure/active-directory/develop/
Libraries to consider:
  - msal (Microsoft Authentication Library)
  - fastapi-azure-auth
"""
from dataclasses import dataclass
from typing import Optional

from fastapi import Request


@dataclass
class User:
    """Represents an authenticated user."""
    email: str
    name: str
    is_approver: bool = False


# -----------------------------------------------------------------
# TODO: Replace this mock implementation with Entra ID authentication
#
# Production implementation should:
# 1. Configure Azure AD app registration
# 2. Use MSAL or fastapi-azure-auth to validate tokens
# 3. Extract user info from validated JWT claims
# 4. Check group membership for approver role
#
# Example with fastapi-azure-auth:
#
#   from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
#
#   azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
#       app_client_id="your-app-client-id",
#       tenant_id="your-tenant-id",
#       scopes={"api://your-app-client-id/user_impersonation": "user_impersonation"},
#   )
#
#   async def get_current_user(
#       request: Request,
#       token: dict = Depends(azure_scheme)
#   ) -> User:
#       return User(
#           email=token.get("preferred_username", ""),
#           name=token.get("name", ""),
#           is_approver="Approvers" in token.get("groups", [])
#       )
# -----------------------------------------------------------------


def get_current_user(request: Request) -> User:
    """
    Get the current authenticated user.

    MVP: Returns mock user for testing.
    Production: Validate Entra ID token and return authenticated user.
    """
    # Check for mock user in session/cookie for testing different roles
    mock_role = request.cookies.get("mock_role", "user")

    if mock_role == "approver":
        return User(
            email="approver@company.com",
            name="Test Approver",
            is_approver=True
        )

    return User(
        email="user@company.com",
        name="Test User",
        is_approver=False
    )


def get_optional_user(request: Request) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    MVP: Always returns a user (no auth required).
    """
    return get_current_user(request)
