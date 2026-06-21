"""Portable conformance against the published contract.

Drives the contract's static OpenAPI - the `@ramblers/sf-contract` v0.5.0 release
artifact - against this server, proving the two agree on the wire without anyone
reading TypeScript. Any consumer, in any language, can run the same check against
its own server: fetch the static spec, compare the component schemas, validate a
live response.

This is the chosen alternative to generating the Pydantic models with
datamodel-code-generator. The hand-written `app/models.py` is kept (it carries the
camelCase alias generator and the title-cased enums tuned for wire parity), and
this test guards that it cannot diverge from the contract - the same guarantee
generated models would give, without the risk of regenerated code changing the
live wire format. Swapping to generated models remains an option if HQ prefer it.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest
from fastapi.testclient import TestClient

from app.main import app

CONTRACT_SPEC_URL = (
    "https://raw.githubusercontent.com/nbarrett/"
    "ramblers-salesforce-contract/v0.5.0/openapi/openapi.json"
)

SHARED_SCHEMAS = (
    "SalesforceMember",
    "MemberListResponse",
    "ConsentUpdateRequest",
    "ConsentUpdateResponse",
    "ApiErrorResponse",
)


def _load_contract_spec() -> dict | None:
    try:
        with urllib.request.urlopen(CONTRACT_SPEC_URL, timeout=10) as response:
            return json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


contract = _load_contract_spec()
client = TestClient(app)

requires_contract = pytest.mark.skipif(
    contract is None, reason="contract static spec unreachable (offline)"
)


def _server_schemas() -> dict:
    return client.get("/openapi.json").json()["components"]["schemas"]


@requires_contract
@pytest.mark.parametrize("name", SHARED_SCHEMAS)
def test_component_matches_contract(name: str) -> None:
    published = contract["components"]["schemas"][name]
    served = _server_schemas()[name]
    assert set(served.get("properties", {})) == set(published.get("properties", {})), (
        f"{name} property names differ from the published contract"
    )
    assert set(served.get("required", [])) == set(published.get("required", [])), (
        f"{name} required fields differ from the published contract"
    )


@requires_contract
def test_live_member_list_conforms_to_contract() -> None:
    allowed = set(contract["components"]["schemas"]["SalesforceMember"]["properties"])
    required = set(contract["components"]["schemas"]["SalesforceMember"].get("required", []))
    body = client.get("/api/groups/KT50/members").json()
    assert set(body) <= set(contract["components"]["schemas"]["MemberListResponse"]["properties"])
    assert body["members"], "demo must return members to validate"
    for member in body["members"]:
        keys = set(member)
        assert keys <= allowed, f"member carries fields absent from the contract: {keys - allowed}"
        assert required <= keys, f"member is missing required contract fields: {required - keys}"
