from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query

from ..auth import require_auth
from ..config import config
from ..errors import ApiException
from ..factory import build_provider
from ..member_provider import (
    ApplyConsentOk,
    ApplyConsentOptions,
    ListMembersOk,
    ListMembersOptions,
    MemberProvider,
)
from ..models import ConsentUpdateRequest, ConsentUpdateResponse, MemberListResponse

router = APIRouter(dependencies=[Depends(require_auth)])

provider: MemberProvider = build_provider()


def _authorise_group(group_code: str) -> None:
    if config.allowed_group_codes and group_code not in config.allowed_group_codes:
        raise ApiException("GROUP_NOT_FOUND", f"Group {group_code} is not served here")


@router.get(
    "/api/groups/{groupCode}/members",
    response_model=MemberListResponse,
    response_model_exclude_none=True,
    summary="List members for a group or area",
)
async def list_members(
    group_code: Annotated[str, Path(alias="groupCode")],
    since: Annotated[Optional[datetime], Query()] = None,
    include_expired: Annotated[Optional[bool], Query(alias="includeExpired")] = None,
) -> MemberListResponse:
    _authorise_group(group_code)
    result = await provider.list_members(
        ListMembersOptions(group_code=group_code, since=since, include_expired=include_expired)
    )
    if isinstance(result, ListMembersOk):
        return result.response
    raise ApiException("GROUP_NOT_FOUND", f"Group {group_code} not found")


@router.post(
    "/api/members/{membershipNumber}/consent",
    response_model=ConsentUpdateResponse,
    response_model_exclude_none=True,
    summary="Consent writeback",
)
async def apply_consent(
    membership_number: Annotated[str, Path(alias="membershipNumber")],
    request: ConsentUpdateRequest,
) -> ConsentUpdateResponse:
    result = await provider.apply_consent(
        ApplyConsentOptions(
            tenant_code=membership_number,
            membership_number=membership_number,
            request=request,
            applied_at=datetime.now(timezone.utc),
        )
    )
    if isinstance(result, ApplyConsentOk):
        return result.response
    raise ApiException("MEMBER_NOT_FOUND", f"Member {membership_number} not found")
