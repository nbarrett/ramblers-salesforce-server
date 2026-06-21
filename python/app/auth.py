"""Inbound request authentication.

Pluggable by configuration - the auth mechanism Ramblers HQ run drops in here
without touching the routes. `AUTH_MODE` chooses the verifier:

  - "entra": validate a Microsoft Entra ID JWT (RS256) against the tenant JWKS,
    checking issuer and audience. This is the app-to-app (OAuth2 client-
    credentials) shape Ramblers HQ's lead developer prefers. To switch it on, HQ
    supply three settings and nothing in the routes changes: AUTH_MODE=entra,
    ENTRA_TENANT_ID and ENTRA_AUDIENCE. The plug-in point is `_verify_entra`.
  - "token": sha256 a long-lived opaque bearer token and compare against an
    allow-list (API_TOKEN_HASHES), matching the mock / TypeScript server.
  - "none" (demo / local default): authentication is not enforced.

The bearer scheme is declared to OpenAPI (`bearer_scheme`), so the Swagger UI at
/docs shows an Authorize button in every mode - HQ can see exactly how a consumer
attaches its token, and paste an Entra access token to try the live endpoints.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Annotated, Optional

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import config
from .errors import ApiException


def entra_openid_configuration_url() -> str:
    """The Entra OIDC discovery document HQ point their token issuer at."""
    tenant = config.entra_tenant_id or "{tenant-id}"
    return f"https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration"


def _scheme_description() -> str:
    if config.auth_mode == "entra":
        return (
            "Microsoft **Entra ID** access token (JWT, RS256). Validated against the "
            "tenant JWKS with issuer and audience checked. OpenID configuration: "
            f"`{entra_openid_configuration_url()}`. Obtain a token from your Entra app "
            "registration (client-credentials flow) and paste it here."
        )
    if config.auth_mode == "token":
        return (
            "Opaque bearer token from the `API_TOKEN_HASHES` allow-list (sha256), "
            "matching the mock and TypeScript server for local parity."
        )
    return (
        "**Demo mode** (`AUTH_MODE=none`): authentication is not enforced on this "
        "deployment. In production set `AUTH_MODE=entra` with `ENTRA_TENANT_ID` and "
        "`ENTRA_AUDIENCE` to require a Microsoft Entra ID JWT. This Authorize button "
        "shows how a consumer attaches its token once auth is switched on."
    )


# Declared to OpenAPI so /docs renders an Authorize button. auto_error=False lets
# demo mode (AUTH_MODE=none) serve unauthenticated while still advertising the scheme.
bearer_scheme = HTTPBearer(
    scheme_name="bearerAuth",
    bearerFormat="JWT",
    auto_error=False,
    description=_scheme_description(),
)


@lru_cache(maxsize=1)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _verify_entra(token: str) -> None:
    # ===================== Entra plug-in point ==========================
    # HQ's auth is Microsoft Entra ID. The body below is the standard OIDC
    # JWT validation; the only inputs HQ provide are the tenant id and the
    # audience (the API's app-registration Application ID URI / client id).
    # Adjust here if HQ's tokens differ - e.g. a v1.0 issuer, or a required
    # scope / role claim to check once the signature verifies.
    # ====================================================================
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


async def require_auth(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)] = None,
) -> None:
    if config.auth_mode == "none":
        return
    if credentials is None or not credentials.credentials:
        raise ApiException("UNAUTHORIZED", "Missing or malformed bearer token")
    token = credentials.credentials
    if config.auth_mode == "entra":
        _verify_entra(token)
    else:
        _verify_opaque(token)
