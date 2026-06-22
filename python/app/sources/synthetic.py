"""In-memory synthetic member source for the demo.

Deterministic: the same group code always yields the same members, so curl,
Swagger and the tests are reproducible. Generates only Salesforce-native fields;
the overlay store owns the extension fields. This is what makes the production
server run and return realistic data with no Salesforce and no database.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from ..models import MemberTerm, SalesforceMember

_FIRST = [
    "Alice", "Bren", "Charlie", "Devi", "Errol", "Fiona", "Gita", "Harpreet",
    "Ivan", "Joan", "Kerry", "Liam", "Mira", "Nuala", "Omar", "Priya",
    "Quentin", "Rosa", "Sam", "Tariq", "Una", "Vikram", "Wendy", "Yusuf",
]
_LAST = [
    "Ashworth", "Brook", "Clegg", "Dunmore", "Ellery", "Frost", "Gledhill",
    "Hargreave", "Ingham", "Jowett", "Kershaw", "Lomax", "Mottram", "Naylor",
    "Otley", "Pickford", "Royle", "Sutcliffe", "Thwaite", "Unwin",
]
_POSTCODES = ["CT1 2AA", "CT2 7NZ", "ME13 7AA", "TN23 1AB", "CT5 3RP", "ME10 4QT"]
_EPOCH = datetime(2026, 6, 1, tzinfo=timezone.utc)


def _member(group_code: str, index: int) -> SalesforceMember:
    first = _FIRST[index % len(_FIRST)]
    last = _LAST[(index * 7) % len(_LAST)]
    term: MemberTerm = "Life" if index % 9 == 0 else "Annual"
    joined = _EPOCH - timedelta(days=400 + index * 17)
    return SalesforceMember(
        salesforce_id=f"003{group_code.upper()}{index:04d}",
        membership_number=f"{group_code.upper()}-{1000 + index}",
        first_name=first,
        last_name=last,
        email=f"{first.lower()}.{last.lower()}@example.org",
        postcode=_POSTCODES[index % len(_POSTCODES)],
        group_name=f"{group_code.upper()} Demo Group",
        group_code=group_code.upper(),
        group_joined_date=joined.isoformat(),
        member_type="Member",
        member_term=term,
        member_status="Active",
        membership_arrangement="Joint" if index % 3 == 0 else "Individual",
        ramblers_joined_date=joined.isoformat(),
        membership_expiry_date=(_EPOCH + timedelta(days=180)).isoformat(),
        email_marketing_consent=(index % 2 == 0),
    )


class SyntheticMemberSource:
    def __init__(self, group_code: str = "KT50", count: int = 20) -> None:
        self._members: dict[str, SalesforceMember] = {}
        self._by_group: dict[str, list[str]] = {}
        self._default_count = count
        self._ensure(group_code)

    def _ensure(self, group_code: str) -> None:
        key = group_code.upper()
        if key in self._by_group:
            return
        numbers: list[str] = []
        for index in range(self._default_count):
            member = _member(key, index)
            assert member.membership_number is not None
            self._members[member.membership_number] = member
            numbers.append(member.membership_number)
        self._by_group[key] = numbers

    def list_members(
        self,
        group_code: str,
        since: Optional[datetime],
        include_expired: Optional[bool],
    ) -> Optional[list[SalesforceMember]]:
        self._ensure(group_code)
        return [self._members[n] for n in self._by_group[group_code.upper()]]

    def find(self, membership_number: str) -> Optional[SalesforceMember]:
        return self._members.get(membership_number)

    def set_email_consent(self, membership_number: str, value: bool) -> bool:
        member = self._members.get(membership_number)
        if member is None:
            return False
        self._members[membership_number] = member.model_copy(
            update={"email_marketing_consent": value}
        )
        return True
