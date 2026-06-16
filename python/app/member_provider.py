"""The seam between HTTP/validation and the Salesforce data layer.

Python equivalent of the contract's MemberProvider port (member-provider.ts).
Results are discriminated unions so a missing group / member is an ordinary
value, not an exception.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol, Union

from .models import ConsentUpdateRequest, ConsentUpdateResponse, MemberListResponse


@dataclass(frozen=True)
class ListMembersOptions:
    group_code: str
    since: Optional[datetime] = None
    include_expired: Optional[bool] = None


@dataclass(frozen=True)
class ApplyConsentOptions:
    tenant_code: str
    membership_number: str
    request: ConsentUpdateRequest
    applied_at: datetime


@dataclass(frozen=True)
class ListMembersOk:
    response: MemberListResponse


@dataclass(frozen=True)
class GroupNotFound:
    pass


@dataclass(frozen=True)
class ApplyConsentOk:
    response: ConsentUpdateResponse


@dataclass(frozen=True)
class MemberNotFound:
    pass


ListMembersResult = Union[ListMembersOk, GroupNotFound]
ApplyConsentResult = Union[ApplyConsentOk, MemberNotFound]


class MemberProvider(Protocol):
    async def list_members(self, options: ListMembersOptions) -> ListMembersResult: ...

    async def apply_consent(self, options: ApplyConsentOptions) -> ApplyConsentResult: ...
