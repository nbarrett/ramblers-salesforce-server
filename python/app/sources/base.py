"""MemberSource: provides the Salesforce-native fields of a member.

The hybrid provider merges overlay attributes on top of whatever a source
returns. Two implementations: SalesforceMemberSource (production, Phase 4) and
SyntheticMemberSource (the in-memory demo). A source returns the extension
fields as None - those are owned by the overlay store, not the source.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol

from ..models import SalesforceMember


class MemberSource(Protocol):
    def list_members(
        self,
        group_code: str,
        since: Optional[datetime],
        include_expired: Optional[bool],
    ) -> Optional[list[SalesforceMember]]: ...

    def find(self, membership_number: str) -> Optional[SalesforceMember]: ...

    def set_email_consent(self, membership_number: str, value: bool) -> bool: ...
