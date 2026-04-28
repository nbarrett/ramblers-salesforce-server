# ramblers-salesforce-server

Production server for the Ramblers Salesforce API. Live at [`salesforce-server.ngx-ramblers.org.uk`](https://salesforce-server.ngx-ramblers.org.uk). Wire format comes from [`@ramblers/sf-contract`](https://github.com/nbarrett/ramblers-salesforce-contract). Companion to [`ramblers-salesforce-mock`](https://github.com/nbarrett/ramblers-salesforce-mock).

> **If you're Ramblers HQ:** the structural plumbing is done. Five concrete functions remain — see the checklist in [#1](https://github.com/nbarrett/ramblers-salesforce-server/issues/1). Once `SF_CLIENT_ID`, `SF_USERNAME`, `SF_JWT_PRIVATE_KEY_PATH`, `API_TOKEN_HASHES` and `ALLOWED_GROUP_CODES` are set as Fly secrets and the five function bodies are filled in, the server returns real Salesforce data instead of `501 NotImplemented` envelopes.

## Status

Scaffolded. The `SalesforceMemberProvider` is wired through to the routes; every method throws `NotImplemented` with structured hints to the file and function HQ needs to fill in. Phase 4 of [_From Mock to Production_](https://www.ngx-ramblers.org.uk/how-to/technical-articles/2026-04-27-salesforce-mock-to-production) fills in the SOQL queries, the JWT signing, and the field mappers.

## One repo of three

| Repo | Role | Live at |
|---|---|---|
| [`ramblers-salesforce-contract`](https://github.com/nbarrett/ramblers-salesforce-contract) | Shared wire-format package — types, Zod schemas, OpenAPI builder, error envelope, columns, port. | git tag `v0.2.0` |
| [`ramblers-salesforce-mock`](https://github.com/nbarrett/ramblers-salesforce-mock) | Mongo-backed development server with admin SPA, xlsx ingest, synthetic data. | [salesforce-mock.ngx-ramblers.org.uk](https://salesforce-mock.ngx-ramblers.org.uk) |
| **`ramblers-salesforce-server`** (this repo) | Salesforce-backed production server. | [salesforce-server.ngx-ramblers.org.uk](https://salesforce-server.ngx-ramblers.org.uk) |

The mock and this server present the byte-identical wire format because both depend on the same contract package. Consumers (NGX-Ramblers, MailMan) point at whichever URL fits their environment.

## Architecture

- Node 20+ and strict TypeScript. No `.js` / `.mjs` / `.cjs` source files.
- Express + jsforce + pino + zod (request validation re-uses the schemas from the contract package).
- **Single Salesforce org**. Tenant boundary via `ALLOWED_GROUP_CODES` env var.
- **Long-lived bearer tokens**. Each token's sha256 hash sits in `API_TOKEN_HASHES`. Not Auth0; not OAuth on the consumer side.
- Deployed to Fly.io (`lhr`, app `ramblers-salesforce-server`).

## Phase 4 checklist (HQ to fill)

| File | Function | What to write |
|---|---|---|
| [`src/salesforce/connection.ts`](src/salesforce/connection.ts) | `buildJwtAssertion` | RS256-sign the JWT bearer assertion using the connected app's private key. Suggested library: `jsonwebtoken` or `jose`. |
| [`src/providers/salesforce-member-provider.ts`](src/providers/salesforce-member-provider.ts) | `SalesforceMemberProvider.listMembers` | SOQL query for the given `groupCode`, mapped to wire shape via `salesforceToMember`. Honour `since` and `includeExpired`. |
| same | `SalesforceMemberProvider.applyConsent` | Composite request: update the Contact's consent fields + insert a `ConsentEvent__c` audit record. |
| same | `salesforceToMember(record)` | Field mapping from a typed Salesforce record to the `SalesforceMember` wire shape. The 36 Insight Hub fields plus the three granular consent flags are documented in [`@ramblers/sf-contract`](https://github.com/nbarrett/ramblers-salesforce-contract). |
| same | `memberToSalesforce(member)` | Reverse mapping for consent writeback. |

The `MemberProvider` interface itself, the `SalesforceMember` shape, the OpenAPI document, and the Zod request schemas all come from the contract package and must not be re-declared here.

## Local development

```sh
corepack enable
pnpm install
cp .env.example .env           # fill in ALLOWED_GROUP_CODES + API_TOKEN_HASHES; SF_* optional
pnpm dev
```

`http://localhost:8080/healthz` returns `{status: "ok", uptime}`. `http://localhost:8080/healthz/salesforce` calls `conn.identity()` when the `SF_*` env vars are set, or returns `503 NOT_CONFIGURED` otherwise.

## Deployment

`pnpm deploy` runs `flyctl deploy`. CI mirrors that on every push to `main`, gated by the `FLY_DEPLOY_ENABLED` repo variable.

Secrets (`API_TOKEN_HASHES`, `SF_CLIENT_ID`, `SF_USERNAME`, `SF_JWT_PRIVATE_KEY_PATH`) live in the NGX staging `config.environments` document — see the `connect-env-db` skill in the NGX-Ramblers repo for the lookup pattern.

## Reading

- [_From Mock to Production_](https://www.ngx-ramblers.org.uk/how-to/technical-articles/2026-04-27-salesforce-mock-to-production) — full architecture write-up: ports & adapters, why three repos, what each one owns.
- [Phase 4 ticket — #1](https://github.com/nbarrett/ramblers-salesforce-server/issues/1) — the concrete checklist for HQ.
- [ngx-ramblers#209 — day-one wire spec](https://github.com/nbarrett/ngx-ramblers/issues/209) — the contract being implemented.
