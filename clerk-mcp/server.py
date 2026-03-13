"""
Clerk MCP Server
=================
Model Context Protocol server that exposes Clerk Backend API operations
as tools for AI assistants.

Tools provided:
- list_users: List users with optional filters
- get_user: Get a single user by ID
- create_user: Create a new user
- update_user: Update user metadata
- delete_user: Delete a user
- search_users: Search users by email or name
- list_sessions: List active sessions for a user
- revoke_session: Revoke a specific session
- get_user_count: Get total user count
- ban_user / unban_user: Ban or unban a user
"""

import os
import json
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load .env from parent directory (project root)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_API_BASE = "https://api.clerk.com/v1"

mcp = FastMCP("Clerk MCP Server")


def _headers() -> dict[str, str]:
    """Build authorization headers for Clerk API."""
    return {
        "Authorization": f"Bearer {CLERK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


async def _clerk_request(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make an authenticated request to the Clerk Backend API."""
    if not CLERK_SECRET_KEY:
        return {"error": "CLERK_SECRET_KEY is not configured. Set it in .env"}

    url = f"{CLERK_API_BASE}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(
            method,
            url,
            headers=_headers(),
            params=params,
            json=json_body,
        )
        if resp.status_code >= 400:
            return {
                "error": f"Clerk API error {resp.status_code}",
                "details": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
            }
        if resp.status_code == 204:
            return {"status": "success"}
        return resp.json()


def _format_user(user: dict) -> dict:
    """Extract key fields from a Clerk user object for cleaner output."""
    email_addresses = user.get("email_addresses", [])
    primary_email = None
    for e in email_addresses:
        if e.get("id") == user.get("primary_email_address_id"):
            primary_email = e.get("email_address")
            break
    if not primary_email and email_addresses:
        primary_email = email_addresses[0].get("email_address")

    return {
        "id": user.get("id"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "email": primary_email,
        "created_at": user.get("created_at"),
        "last_sign_in_at": user.get("last_sign_in_at"),
        "banned": user.get("banned", False),
        "public_metadata": user.get("public_metadata", {}),
        "private_metadata": user.get("private_metadata", {}),
    }


# ── User Management Tools ──────────────────────────────────────────────


@mcp.tool()
async def list_users(
    limit: int = 10,
    offset: int = 0,
    order_by: str = "-created_at",
) -> str:
    """List Clerk users with pagination.

    Args:
        limit: Maximum number of users to return (1-100, default 10)
        offset: Number of users to skip for pagination
        order_by: Sort order. Use '-created_at' for newest first, '+created_at' for oldest first
    """
    result = await _clerk_request(
        "GET",
        "/users",
        params={"limit": min(limit, 100), "offset": offset, "order_by": order_by},
    )
    if isinstance(result, list):
        users = [_format_user(u) for u in result]
        return json.dumps({"users": users, "count": len(users)}, indent=2)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_user(user_id: str) -> str:
    """Get detailed information about a specific Clerk user.

    Args:
        user_id: The Clerk user ID (e.g. 'user_2abc123')
    """
    result = await _clerk_request("GET", f"/users/{user_id}")
    if "error" in result:
        return json.dumps(result, indent=2)
    return json.dumps(_format_user(result), indent=2)


@mcp.tool()
async def search_users(query: str) -> str:
    """Search for Clerk users by email address or name.

    Args:
        query: Search query - can be an email address or name
    """
    # Clerk API supports email_address and query params
    result = await _clerk_request(
        "GET",
        "/users",
        params={"query": query, "limit": 20},
    )
    if isinstance(result, list):
        users = [_format_user(u) for u in result]
        return json.dumps({"users": users, "count": len(users)}, indent=2)
    return json.dumps(result, indent=2)


@mcp.tool()
async def create_user(
    email_address: str,
    first_name: str = "",
    last_name: str = "",
    password: str = "",
) -> str:
    """Create a new Clerk user.

    Args:
        email_address: The user's email address (required)
        first_name: The user's first name
        last_name: The user's last name
        password: The user's password (if using password-based auth)
    """
    body: dict[str, Any] = {
        "email_address": [email_address],
    }
    if first_name:
        body["first_name"] = first_name
    if last_name:
        body["last_name"] = last_name
    if password:
        body["password"] = password

    result = await _clerk_request("POST", "/users", json_body=body)
    if "error" in result:
        return json.dumps(result, indent=2)
    return json.dumps(_format_user(result), indent=2)


@mcp.tool()
async def update_user(
    user_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    public_metadata: str | None = None,
    private_metadata: str | None = None,
) -> str:
    """Update a Clerk user's profile or metadata.

    Args:
        user_id: The Clerk user ID to update
        first_name: New first name (optional)
        last_name: New last name (optional)
        public_metadata: JSON string of public metadata to set (optional)
        private_metadata: JSON string of private metadata to set (optional)
    """
    body: dict[str, Any] = {}
    if first_name is not None:
        body["first_name"] = first_name
    if last_name is not None:
        body["last_name"] = last_name
    if public_metadata is not None:
        body["public_metadata"] = json.loads(public_metadata)
    if private_metadata is not None:
        body["private_metadata"] = json.loads(private_metadata)

    if not body:
        return json.dumps({"error": "No fields to update"})

    result = await _clerk_request("PATCH", f"/users/{user_id}", json_body=body)
    if "error" in result:
        return json.dumps(result, indent=2)
    return json.dumps(_format_user(result), indent=2)


@mcp.tool()
async def delete_user(user_id: str) -> str:
    """Delete a Clerk user permanently.

    Args:
        user_id: The Clerk user ID to delete
    """
    result = await _clerk_request("DELETE", f"/users/{user_id}")
    return json.dumps(result, indent=2)


@mcp.tool()
async def ban_user(user_id: str) -> str:
    """Ban a Clerk user, preventing them from signing in.

    Args:
        user_id: The Clerk user ID to ban
    """
    result = await _clerk_request("POST", f"/users/{user_id}/ban")
    if "error" in result:
        return json.dumps(result, indent=2)
    return json.dumps(_format_user(result), indent=2)


@mcp.tool()
async def unban_user(user_id: str) -> str:
    """Unban a previously banned Clerk user.

    Args:
        user_id: The Clerk user ID to unban
    """
    result = await _clerk_request("POST", f"/users/{user_id}/unban")
    if "error" in result:
        return json.dumps(result, indent=2)
    return json.dumps(_format_user(result), indent=2)


@mcp.tool()
async def get_user_count() -> str:
    """Get the total number of users in the Clerk application."""
    result = await _clerk_request("GET", "/users/count")
    return json.dumps(result, indent=2)


# ── Session Management Tools ───────────────────────────────────────────


@mcp.tool()
async def list_sessions(
    user_id: str = "",
    status: str = "active",
    limit: int = 20,
) -> str:
    """List Clerk sessions with optional filters.

    Args:
        user_id: Filter sessions by user ID (optional)
        status: Filter by status: 'active', 'revoked', 'ended', 'expired', 'removed', 'abandoned' (default: 'active')
        limit: Maximum number of sessions to return (default 20)
    """
    params: dict[str, Any] = {"status": status, "limit": min(limit, 100)}
    if user_id:
        params["user_id"] = user_id

    result = await _clerk_request("GET", "/sessions", params=params)
    if isinstance(result, list):
        sessions = [
            {
                "id": s.get("id"),
                "user_id": s.get("user_id"),
                "status": s.get("status"),
                "last_active_at": s.get("last_active_at"),
                "expire_at": s.get("expire_at"),
                "created_at": s.get("created_at"),
            }
            for s in result
        ]
        return json.dumps({"sessions": sessions, "count": len(sessions)}, indent=2)
    return json.dumps(result, indent=2)


@mcp.tool()
async def revoke_session(session_id: str) -> str:
    """Revoke a specific Clerk session, forcing the user to re-authenticate.

    Args:
        session_id: The session ID to revoke
    """
    result = await _clerk_request("POST", f"/sessions/{session_id}/revoke")
    return json.dumps(result, indent=2)


# ── Organization Tools ─────────────────────────────────────────────────


@mcp.tool()
async def list_organizations(limit: int = 20, offset: int = 0) -> str:
    """List Clerk organizations.

    Args:
        limit: Maximum number of organizations to return (default 20)
        offset: Number of organizations to skip for pagination
    """
    result = await _clerk_request(
        "GET",
        "/organizations",
        params={"limit": min(limit, 100), "offset": offset},
    )
    if isinstance(result, dict) and "data" in result:
        orgs = [
            {
                "id": o.get("id"),
                "name": o.get("name"),
                "slug": o.get("slug"),
                "members_count": o.get("members_count"),
                "created_at": o.get("created_at"),
            }
            for o in result["data"]
        ]
        return json.dumps({"organizations": orgs, "total": result.get("total_count", len(orgs))}, indent=2)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_organization(organization_id: str) -> str:
    """Get details of a specific Clerk organization.

    Args:
        organization_id: The organization ID
    """
    result = await _clerk_request("GET", f"/organizations/{organization_id}")
    return json.dumps(result, indent=2)


# ── Invitation Tools ────────────────────────────────────────────────────


@mcp.tool()
async def create_invitation(
    email_address: str,
    public_metadata: str = "{}",
    redirect_url: str = "",
) -> str:
    """Create an invitation for a new user.

    Args:
        email_address: Email to send the invitation to
        public_metadata: JSON string of public metadata for the invited user
        redirect_url: URL to redirect to after accepting the invitation
    """
    body: dict[str, Any] = {
        "email_address": email_address,
    }
    if public_metadata != "{}":
        body["public_metadata"] = json.loads(public_metadata)
    if redirect_url:
        body["redirect_url"] = redirect_url

    result = await _clerk_request("POST", "/invitations", json_body=body)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_invitations(status: str = "pending", limit: int = 20) -> str:
    """List invitations.

    Args:
        status: Filter by status: 'pending', 'accepted', 'revoked' (default: 'pending')
        limit: Maximum number to return
    """
    result = await _clerk_request(
        "GET",
        "/invitations",
        params={"status": status, "limit": min(limit, 100)},
    )
    if isinstance(result, dict) and "data" in result:
        invites = result["data"]
    elif isinstance(result, list):
        invites = result
    else:
        return json.dumps(result, indent=2)

    formatted = [
        {
            "id": i.get("id"),
            "email_address": i.get("email_address"),
            "status": i.get("status"),
            "created_at": i.get("created_at"),
        }
        for i in invites
    ]
    return json.dumps({"invitations": formatted, "count": len(formatted)}, indent=2)


@mcp.tool()
async def revoke_invitation(invitation_id: str) -> str:
    """Revoke a pending invitation.

    Args:
        invitation_id: The invitation ID to revoke
    """
    result = await _clerk_request("POST", f"/invitations/{invitation_id}/revoke")
    return json.dumps(result, indent=2)


# ── Run the server ──────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
