"""Inbound request authentication.

Two modes, chosen by AUTH_MODE:
  - "entra"  (default): validate a Microsoft Entra ID JWT (RS256) against the
    tenant JWKS, checking issuer and audience. This is the app-to-app
    (OAuth2 client-credentials) shape Ramblers HQ's lead developer prefers.
  - "token": sha256 a long-lived opaque bearer token and compare against an
    allow-list, matching the mock / TypeScript server for local parity.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Annotated, Optional

import jwt
from fastapi import Header
from jwt import PyJWKClient

from .config import config
from .errors import ApiException


def _bearer(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiException("UNAUTHORIZED", "Missing or malformed bearer token")
    return authorization[7:].strip()


@lru_cache(maxsize=1)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _verify_entra(token: str) -> None:
    if not config.entra_tenant_id or not config.entra_audience:
        raise ApiException("INTERNAL_ERROR", "Entra auth is not configured")
    jwks_url = f"https://login.microsoftonline.com/{config.entra_tenant_id}/discovery/v2.0/keys"
    issuer = f"https://login.microsoftonline.com/{config.entra_tenant_id}/v2.0"
    try:
        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
        jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=config.entra_audience,
            issuer=issuer,
        )
    except ApiException:
        raise
    except Exception as exc:
        raise ApiException("UNAUTHORIZED", "Invalid Entra token") from exc


def _verify_opaque(token: str) -> None:
    digest = hashlib.sha256(token.encode()).hexdigest()
    if not config.api_token_hashes or digest not in config.api_token_hashes:
        raise ApiException("UNAUTHORIZED", "Invalid token")


async def require_auth(authorization: Annotated[Optional[str], Header()] = None) -> None:
    if config.auth_mode == "none":
        return
    token = _bearer(authorization)
    if config.auth_mode == "entra":
        _verify_entra(token)
    else:
        _verify_opaque(token)
