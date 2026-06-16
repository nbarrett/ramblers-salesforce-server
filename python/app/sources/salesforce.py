"""Salesforce member source - scaffolded, bodies raise NotImplementedError.

Phase 4 (Ramblers HQ) fills these in. A source returns only the Salesforce-native
fields; the hybrid provider merges the overlay attributes, so these queries never
touch preferredName or the granular consent flags.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..models import SalesforceMember


class SalesforceMemberSource:
    def __init__(self, connection: object = None) -> None:
        self._connection = connection

    def list_members(
        self,
        group_code: str,
        since: Optional[datetime],
        include_expired: Optional[bool],
    ) -> Optional[list[SalesforceMember]]:
        raise NotImplementedError(
            "Phase 4 (Ramblers HQ): SOQL query for the group's Contacts, mapped to "
            "SalesforceMember (Salesforce-native fields only). Return None if the group "
            "is unknown. Honour `since` for incremental sync and `include_expired`."
        )

    def find(self, membership_number: str) -> Optional[SalesforceMember]:
        raise NotImplementedError(
            "Phase 4 (Ramblers HQ): SOQL lookup of one member by membership number."
        )

    def set_email_consent(self, membership_number: str, value: bool) -> bool:
        raise NotImplementedError(
            "Phase 4 (Ramblers HQ): update the member's Salesforce-native "
            "emailMarketingConsent field. Return False if the member is unknown."
        )
