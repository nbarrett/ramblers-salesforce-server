"""Overlay store: a cheap side-database for member attributes Salesforce charges
to hold.

Each attribute lives in exactly one authoritative place - Salesforce or here -
never both. The hybrid provider reads the Salesforce-native fields from the
member source and merges these overlay attributes on top, keyed by the member's
salesforceId, so consumers still see one unified member in the contract shape.

OVERLAY_FIELDS lists the Pydantic field names this store owns. They map to the
contract's extension fields (the ones #209 marks "New - HQ must create in
Salesforce"): preferredName and the three granular marketing-consent flags.
"""

from __future__ import annotations

from typing import Protocol

OVERLAY_FIELDS = (
    "preferred_name",
    "group_marketing_consent",
    "area_marketing_consent",
    "other_marketing_consent",
)


class OverlayStore(Protocol):
    def read(self, salesforce_id: str) -> dict[str, object]: ...

    def read_many(self, salesforce_ids: list[str]) -> dict[str, dict[str, object]]: ...

    def write(self, salesforce_id: str, attributes: dict[str, object]) -> None: ...

    def delete(self, salesforce_id: str) -> None: ...
