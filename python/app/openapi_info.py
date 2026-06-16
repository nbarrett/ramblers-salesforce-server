# ruff: noqa: E501
"""Rich OpenAPI description and contact, rendered as Markdown in the Swagger UI (/docs)."""

CONTACT = {
    "name": "ramblers-salesforce-server",
    "url": "https://github.com/nbarrett/ramblers-salesforce-server",
}

DESCRIPTION = """\
## Try it out

This deployment runs in **demo mode** - synthetic data, no Salesforce, no authentication - so every endpoint below is live right now:

**→ [List members for a demo group](/api/groups/KT50/members)** - 20 synthetic members in the exact contract wire shape.<br>
**→ Try `POST /api/members/{membershipNumber}/consent`** - record a consent change against a member such as `KT50-1000`.<br>
**→ [Raw openapi.json](/openapi.json)** - the document this page is rendered from.

## Reference

**→ [ramblers-salesforce-server on GitHub](https://github.com/nbarrett/ramblers-salesforce-server)** - this server's source; the Python and TypeScript implementations sit side by side.<br>
**→ [nbarrett/ngx-ramblers#209](https://github.com/nbarrett/ngx-ramblers/issues/209)** - the day-one API contract both servers conform to.<br>
**→ [nbarrett/ngx-ramblers#211](https://github.com/nbarrett/ngx-ramblers/issues/211)** - Phase 2 spec (training, area aggregates, accreditation).<br>
**→ [@ramblers/sf-contract](https://github.com/nbarrett/ramblers-salesforce-contract)** - the shared wire-format package both servers consume.<br>
**→ [Mock server](https://salesforce-mock.ngx-ramblers.org.uk/docs)** - the shared development fixture, with an admin console and synthetic data.

## What this is

A Python / FastAPI reference implementation of the Ramblers Salesforce member API, for the Python / Azure / Entra stack. Behind one contract it composes Salesforce with a cheap **overlay store** for the attributes Salesforce charges to hold (`HybridMemberProvider`), so consumers always see one unified member. In production it talks to Salesforce; here it serves synthetic demo data. The only work left for the data owner is three methods in the Salesforce source (Phase 4).
"""
