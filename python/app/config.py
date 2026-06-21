from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Config:
    provider: str = field(default_factory=lambda: os.environ.get("PROVIDER", "demo"))
    demo_group_code: str = field(default_factory=lambda: os.environ.get("DEMO_GROUP_CODE", "KT50"))
    auth_mode: str = field(default_factory=lambda: os.environ.get("AUTH_MODE", "none"))
    allowed_group_codes: list[str] = field(
        default_factory=lambda: _split(os.environ.get("ALLOWED_GROUP_CODES", ""))
    )
    api_token_hashes: list[str] = field(
        default_factory=lambda: _split(os.environ.get("API_TOKEN_HASHES", ""))
    )
    entra_tenant_id: str = field(default_factory=lambda: os.environ.get("ENTRA_TENANT_ID", ""))
    entra_audience: str = field(default_factory=lambda: os.environ.get("ENTRA_AUDIENCE", ""))
    overlay_connection_string: str = field(
        default_factory=lambda: os.environ.get("OVERLAY_CONNECTION_STRING", "")
    )
    overlay_table_name: str = field(
        default_factory=lambda: os.environ.get("OVERLAY_TABLE_NAME", "memberoverlay")
    )
    public_base_url: str = field(
        default_factory=lambda: os.environ.get("PUBLIC_BASE_URL", "/")
    )


config = Config()
