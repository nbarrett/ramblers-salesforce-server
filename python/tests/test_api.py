"""End-to-end HTTP tests through the real FastAPI app (demo mode by default).

Proves the live behaviour a consumer sees: the demo serves data in the contract
wire shape, the bare URL points at the docs, errors use the contract envelope,
the consent writeback round-trips, and the auth layer rejects bad tokens.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth import _verify_opaque
from app.errors import ApiException
from app.main import app

client = TestClient(app)


def test_root_redirects_to_docs() -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_health_ok() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_members_serves_demo_data_in_wire_shape() -> None:
    response = client.get("/api/groups/KT50/members")
    assert response.status_code == 200
    body = response.json()
    assert body["groupCode"] == "KT50"
    assert body["totalCount"] == 20
    first = body["members"][0]
    assert "salesforceId" in first
    assert "ramblersJoinedDate" in first
    assert first["memberTerm"] in ("Annual", "Life")
    assert "membershipType" not in first


def test_unknown_member_consent_returns_404_envelope() -> None:
    response = client.post(
        "/api/members/NOPE-1/consent",
        json={
            "groupMarketingConsent": True,
            "source": "ngx-ramblers",
            "timestamp": "2026-06-16T00:00:00Z",
        },
    )
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "MEMBER_NOT_FOUND"
    assert "timestamp" in body


def test_consent_writeback_round_trips() -> None:
    response = client.post(
        "/api/members/KT50-1000/consent",
        json={
            "groupMarketingConsent": True,
            "source": "ngx-ramblers",
            "timestamp": "2026-06-16T00:00:00Z",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["membershipNumber"] == "KT50-1000"
    assert body["groupMarketingConsent"] is True
    assert body["success"] is True


def test_opaque_auth_rejects_unknown_token() -> None:
    with pytest.raises(ApiException):
        _verify_opaque("definitely-not-a-valid-token")
