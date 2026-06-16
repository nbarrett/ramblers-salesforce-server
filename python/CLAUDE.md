# CLAUDE.md

## Critical Rules

1. **NEVER commit or push without explicit instruction** — make file changes freely; `git commit` and `git push` each need the user to explicitly ask.
2. **No AI attribution in commits** — no `Co-Authored-By`, no `Generated with`.
3. **Wire format comes from `@ramblers/sf-contract`** — `app/models.py` mirrors the contract's JSON Schema. Never invent wire fields here. When the contract tag bumps, regenerate / re-check the models and run the conformance tests.
4. **Parallel to the TypeScript server** — this server and the sibling `typescript/` server must stay byte-identical on the wire. A route or field here that the contract does not define is a bug.
5. **Phase 4 is HQ's** — the Salesforce source bodies in `app/sources/salesforce.py` stay `NotImplementedError` until Ramblers HQ fill them in. The overlay store, the hybrid merge, routing, validation, auth and OpenAPI are done.

## Project Overview

- **Purpose**: Python / FastAPI / Azure Functions reference implementation of the Ramblers Salesforce member API (ngx-ramblers#209), for HQ to adopt in their preferred stack (Python, Azure, Entra).
- **Runtime**: Python 3.9+ (Azure Functions Python v2 programming model), FastAPI, Pydantic v2, PyJWT, simple-salesforce.
- **Entry points**: `app/main.py` (the FastAPI app, for local `uvicorn`) and `function_app.py` (the Azure Functions ASGI host).

## Code Style

- **snake_case** for Python identifiers; the camelCase JSON wire names come from the Pydantic alias generator, not from the field names.
- **Type hints everywhere**; `mypy --strict` must pass.
- **`ruff`** for lint + import order.
- **UK English** in prose.
- **Minimal, scoped changes.**

## Git Workflow

- **Conventional commits**: `<type>(<scope>): <description>`
- **Paragraph-style body** explaining the change.
- **Trunk-based on `main`** — no PRs, no branches, no worktrees.
- **No literal `\n`** in commit messages.

## Commands

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check .                 # lint
mypy app                     # types
pytest                       # conformance + unit tests
uvicorn app.main:app --reload --port 7071   # local ASGI
func start                   # local Azure Functions host (needs Core Tools)
```

## Auth

`AUTH_MODE=entra` (default) validates Entra ID JWTs (RS256) against the tenant JWKS, checking issuer + audience. `AUTH_MODE=token` compares a sha256 of the bearer token against `API_TOKEN_HASHES`, for local parity with the mock. Per-deployment access is the `ALLOWED_GROUP_CODES` allow-list (the per-client token model from #209).
