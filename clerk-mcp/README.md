# Clerk MCP Server

An MCP (Model Context Protocol) server that exposes Clerk user management and authentication operations as tools for AI assistants in VS Code / GitHub Copilot.

## Tools Available

### User Management
| Tool | Description |
|------|-------------|
| `list_users` | List users with pagination and sorting |
| `get_user` | Get detailed info for a specific user |
| `search_users` | Search users by email or name |
| `create_user` | Create a new user |
| `update_user` | Update user profile and metadata |
| `delete_user` | Permanently delete a user |
| `ban_user` | Ban a user from signing in |
| `unban_user` | Unban a previously banned user |
| `get_user_count` | Get total registered user count |

### Session Management
| Tool | Description |
|------|-------------|
| `list_sessions` | List sessions with filters (user, status) |
| `revoke_session` | Revoke a session to force re-auth |

### Organization Management
| Tool | Description |
|------|-------------|
| `list_organizations` | List all organizations |
| `get_organization` | Get details of a specific organization |

### Invitations
| Tool | Description |
|------|-------------|
| `create_invitation` | Send an invitation to a new user |
| `list_invitations` | List invitations by status |
| `revoke_invitation` | Revoke a pending invitation |

## Setup

1. Install dependencies:
   ```bash
   cd clerk-mcp
   pip install -e .
   ```

2. Ensure your `.env` in the project root has `CLERK_SECRET_KEY` set.

3. The MCP server is configured in `.vscode/mcp.json` and starts automatically when VS Code loads the workspace.

## Manual Testing

```bash
cd clerk-mcp
python server.py
```

The server communicates over stdio using the MCP protocol.
