"""Wire-format models for the Ramblers Salesforce API.

Mirrors @ramblers/sf-contract v0.4.0 (ngx-ramblers#209). Python field names are
snake_case; the JSON wire names are camelCase, produced by the shared alias
generator. Regenerate / re-check these whenever the contract tag bumps.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

MemberTerm = Literal["Annual", "Life"]
ChangeType = Literal["added", "updated", "removed"]
RemovalReason = Literal["expired", "transferred", "deceased", "other"]
ConsentSource = Literal["ngx-ramblers", "mailman"]
ApiErrorCode = Literal[
    "UNAUTHORIZED",
    "GROUP_NOT_FOUND",
    "MEMBER_NOT_FOUND",
    "BAD_REQUEST",
    "RATE_LIMITED",
    "INTERNAL_ERROR",
]


class WireModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class GroupMembershipRoles(WireModel):
    walk_leader: Optional[bool] = None
    email_sender: Optional[bool] = None
    view_membership_data: Optional[bool] = None


class GroupMembership(WireModel):
    group_code: str
    primary: bool
    roles: Optional[GroupMembershipRoles] = None


class AreaMembershipRoles(WireModel):
    email_sender: Optional[bool] = None


class AreaMembership(WireModel):
    area_code: str
    roles: Optional[AreaMembershipRoles] = None


class SalesforceMember(WireModel):
    salesforce_id: str
    membership_number: Optional[str] = None
    first_name: Optional[str] = None
    preferred_name: Optional[str] = None
    initials: Optional[str] = None
    last_name: str
    title: Optional[str] = None

    email: Optional[str] = None
    mobile_number: Optional[str] = None
    landline_telephone: Optional[str] = None

    address1: Optional[str] = None
    address2: Optional[str] = None
    address3: Optional[str] = None
    town: Optional[str] = None
    county: Optional[str] = None
    country: Optional[str] = None
    postcode: Optional[str] = None

    group_name: Optional[str] = None
    group_code: Optional[str] = None
    group_joined_date: Optional[str] = None
    member_type: Optional[str] = None
    member_term: Optional[MemberTerm] = None
    member_status: Optional[str] = None
    membership_arrangement: Optional[str] = None
    joint_with: Optional[str] = None
    membership_expiry_date: Optional[str] = None
    ramblers_joined_date: Optional[str] = None

    area_name: Optional[str] = None
    area_joined_date: Optional[str] = None

    group_memberships: Optional[list[GroupMembership]] = None
    area_memberships: Optional[list[AreaMembership]] = None

    volunteer: Optional[bool] = None
    affiliate_member_primary_group: Optional[str] = None

    email_marketing_consent: bool
    email_permission_last_updated: Optional[str] = None
    post_direct_marketing: Optional[bool] = None
    post_permission_last_updated: Optional[str] = None
    telephone_direct_marketing: Optional[bool] = None
    telephone_permission_last_updated: Optional[str] = None
    walk_programme_opt_out: Optional[bool] = None

    group_marketing_consent: Optional[bool] = None
    area_marketing_consent: Optional[bool] = None
    other_marketing_consent: Optional[bool] = None


class MemberChange(WireModel):
    member: SalesforceMember
    change_type: ChangeType
    changed_at: str
    removal_reason: Optional[RemovalReason] = None


class MemberListResponse(WireModel):
    group_code: str
    group_name: str
    total_count: int
    since: Optional[str] = None
    members: list[SalesforceMember]
    changes: Optional[list[MemberChange]] = None


class ConsentUpdateRequest(WireModel):
    email_marketing_consent: Optional[bool] = None
    group_marketing_consent: Optional[bool] = None
    area_marketing_consent: Optional[bool] = None
    other_marketing_consent: Optional[bool] = None
    source: ConsentSource
    timestamp: str
    reason: Optional[str] = None


class ConsentUpdateResponse(WireModel):
    membership_number: str
    email_marketing_consent: Optional[bool] = None
    group_marketing_consent: Optional[bool] = None
    area_marketing_consent: Optional[bool] = None
    other_marketing_consent: Optional[bool] = None
    updated_at: str
    success: bool


class ApiError(WireModel):
    code: ApiErrorCode
    message: str
    details: Optional[dict[str, object]] = None


class ApiErrorResponse(WireModel):
    error: ApiError
    timestamp: str
