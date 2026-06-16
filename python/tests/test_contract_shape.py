"""Conformance checks: the Python server's wire shape must match sf-contract v0.4.0.

These assert the OpenAPI document this server generates carries the v0.4.0 field
names and value vocabularies, so the Python and TypeScript servers stay
byte-identical from a consumer's point of view.
"""

from __future__ import annotations

from app.main import app
from app.models import SalesforceMember


def _member_schema() -> dict:
    return app.openapi()["components"]["schemas"]["SalesforceMember"]


def test_paths_match_contract() -> None:
    paths = app.openapi()["paths"]
    assert "/api/groups/{groupCode}/members" in paths
    assert "/api/members/{membershipNumber}/consent" in paths


def test_v040_field_renames_present() -> None:
    props = _member_schema()["properties"]
    assert "ramblersJoinedDate" in props
    assert "membershipArrangement" in props
    assert "ramblersJoinDate" not in props
    assert "membershipType" not in props


def _find_enum(schema: dict) -> list:
    if "enum" in schema:
        return schema["enum"]
    for branch in schema.get("anyOf", []) + schema.get("allOf", []):
        found = _find_enum(branch)
        if found:
            return found
    return []


def test_member_term_is_title_case() -> None:
    enum = _find_enum(_member_schema()["properties"]["memberTerm"])
    assert set(enum) == {"Annual", "Life"}


def test_required_fields() -> None:
    required = set(_member_schema()["required"])
    assert {"salesforceId", "lastName", "emailMarketingConsent"} <= required


def test_member_serialises_with_camelcase_aliases() -> None:
    member = SalesforceMember(
        salesforce_id="003AA",
        last_name="Bigley",
        email_marketing_consent=True,
        ramblers_joined_date="2019-07-29T00:00:00Z",
        membership_arrangement="Individual",
        member_term="Annual",
    )
    wire = member.model_dump(by_alias=True, exclude_none=True)
    assert wire["salesforceId"] == "003AA"
    assert wire["ramblersJoinedDate"] == "2019-07-29T00:00:00Z"
    assert wire["membershipArrangement"] == "Individual"
    assert wire["memberTerm"] == "Annual"
