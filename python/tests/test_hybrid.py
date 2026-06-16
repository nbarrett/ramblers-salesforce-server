"""Hybrid provider: proves the Salesforce-native fields and the overlay fields
merge into one member, and that a consent write is split to the right home.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.member_provider import (
    ApplyConsentOk,
    ApplyConsentOptions,
    ListMembersOk,
    ListMembersOptions,
    MemberNotFound,
)
from app.models import ConsentUpdateRequest
from app.overlay.memory import InMemoryOverlayStore
from app.providers.hybrid_member_provider import HybridMemberProvider
from app.sources.synthetic import SyntheticMemberSource


def _provider() -> HybridMemberProvider:
    return HybridMemberProvider(SyntheticMemberSource(group_code="KT50"), InMemoryOverlayStore())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_demo_list_returns_base_fields_without_overlay() -> None:
    result = asyncio.run(_provider().list_members(ListMembersOptions(group_code="KT50")))
    assert isinstance(result, ListMembersOk)
    members = result.response.members
    assert len(members) == 20
    first = members[0]
    assert first.salesforce_id and first.last_name
    assert first.member_term in ("Annual", "Life")
    assert first.preferred_name is None
    assert first.group_marketing_consent is None


def test_consent_splits_across_salesforce_and_overlay() -> None:
    provider = _provider()
    listed = asyncio.run(provider.list_members(ListMembersOptions(group_code="KT50")))
    assert isinstance(listed, ListMembersOk)
    number = listed.response.members[0].membership_number
    assert number is not None

    request = ConsentUpdateRequest(
        email_marketing_consent=False,
        group_marketing_consent=True,
        area_marketing_consent=False,
        source="ngx-ramblers",
        timestamp=_now(),
    )
    applied = asyncio.run(
        provider.apply_consent(
            ApplyConsentOptions(
                tenant_code=number,
                membership_number=number,
                request=request,
                applied_at=datetime.now(timezone.utc),
            )
        )
    )
    assert isinstance(applied, ApplyConsentOk)
    assert applied.response.group_marketing_consent is True
    assert applied.response.area_marketing_consent is False

    relisted = asyncio.run(provider.list_members(ListMembersOptions(group_code="KT50")))
    assert isinstance(relisted, ListMembersOk)
    same = next(m for m in relisted.response.members if m.membership_number == number)
    assert same.group_marketing_consent is True
    assert same.email_marketing_consent is False


def test_unknown_member_is_member_not_found() -> None:
    request = ConsentUpdateRequest(source="mailman", timestamp=_now())
    result = asyncio.run(
        _provider().apply_consent(
            ApplyConsentOptions(
                tenant_code="X",
                membership_number="NOPE-1",
                request=request,
                applied_at=datetime.now(timezone.utc),
            )
        )
    )
    assert isinstance(result, MemberNotFound)
