from dataclasses import dataclass

import httpx
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from app.config import settings

_jwks_cache: dict | None = None


@dataclass
class AuthUser:
    user_id: str
    email: str | None = None
    role: str | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.clerk_jwks_url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        return _jwks_cache


def _extract_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    return auth_header[7:]


async def get_current_user(request: Request) -> AuthUser:
    token = _extract_token(request)

    # In development, allow a bypass token for testing
    if settings.clerk_secret_key == "" and token == "dev-token":
        return AuthUser(user_id="dev-user", email="dev@example.com", role="admin")

    try:
        jwks = await _get_jwks()
        # Get the signing key from JWKS
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find signing key",
            )

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )

        return AuthUser(
            user_id=user_id,
            email=payload.get("email"),
            role=payload.get("metadata", {}).get("role", "user"),
        )

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )
