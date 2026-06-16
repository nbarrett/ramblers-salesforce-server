"""HybridMemberProvider: the answer to "Salesforce is expensive about custom data".

Composes a MemberSource (Salesforce-native fields) with an OverlayStore (the
extension fields Salesforce charges to hold) behind the contract's MemberProvider
port. Consumers still see one unified member; whether a field lives in Salesforce
or in the cheap overlay store is an implementation detail they never observe.

Each attribute has one authoritative home, set by the manifest in overlay.store:
the source owns the Salesforce-native fields, the overlay owns OVERLAY_FIELDS.
Nothing is written to both.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ..member_provider import (
    ApplyConsentOk,
    ApplyConsentOptions,
    ApplyConsentResult,
    GroupNotFound,
    ListMembersOk,
    ListMembersOptions,
    ListMembersResult,
    MemberNotFound,
)
from ..models import ConsentUpdateResponse, MemberListResponse, SalesforceMember
from ..overlay.store import OVERLAY_FIELDS, OverlayStore
from ..sources.base import MemberSource

_CONSENT_OVERLAY = (
    "group_marketing_consent",
    "area_marketing_consent",
    "other_marketing_consent",
)


def _as_bool(value: object) -> Optional[bool]:
    return value if isinstance(value, bool) else None


class HybridMemberProvider:
    def __init__(self, source: MemberSource, overlay: OverlayStore) -> None:
        self._source = source
        self._overlay = overlay

    async def list_members(self, options: ListMembersOptions) -> ListMembersResult:
        base = self._source.list_members(
            options.group_code, options.since, options.include_expired
        )
        if base is None:
            return GroupNotFound()
        overlays = self._overlay.read_many([m.salesforce_id for m in base])
        merged = [self._merge(m, overlays.get(m.salesforce_id, {})) for m in base]
        group_name = merged[0].group_name if merged and merged[0].group_name else options.group_code
        response = MemberListResponse(
            group_code=options.group_code,
            group_name=group_name,
            total_count=len(merged),
            members=merged,
        )
        return ListMembersOk(response=response)

    async def apply_consent(self, options: ApplyConsentOptions) -> ApplyConsentResult:
        member = self._source.find(options.membership_number)
        if member is None:
            return MemberNotFound()
        request = options.request
        if request.email_marketing_consent is not None:
            self._source.set_email_consent(
                options.membership_number, request.email_marketing_consent
            )
        overlay_update = {
            field: getattr(request, field)
            for field in _CONSENT_OVERLAY
            if getattr(request, field) is not None
        }
        if overlay_update:
            self._overlay.write(member.salesforce_id, overlay_update)
        stored = self._overlay.read(member.salesforce_id)
        response = ConsentUpdateResponse(
            membership_number=options.membership_number,
            email_marketing_consent=request.email_marketing_consent,
            group_marketing_consent=_as_bool(stored.get("group_marketing_consent")),
            area_marketing_consent=_as_bool(stored.get("area_marketing_consent")),
            other_marketing_consent=_as_bool(stored.get("other_marketing_consent")),
            updated_at=datetime.now(timezone.utc).isoformat(),
            success=True,
        )
        return ApplyConsentOk(response=response)

    def _merge(self, member: SalesforceMember, overlay: dict[str, object]) -> SalesforceMember:
        update = {field: overlay[field] for field in OVERLAY_FIELDS if field in overlay}
        return member.model_copy(update=update) if update else member
