# ramblers-salesforce-server

Production server for the Ramblers Salesforce API. Companion to [`ramblers-salesforce-mock`](https://github.com/nbarrett/ramblers-salesforce-mock). Wire format comes from [`@ramblers/sf-contract`](https://github.com/nbarrett/ramblers-salesforce-contract).

**Status:** scaffolded. The `SalesforceMemberProvider` is wired up to the routes but every method throws `NotImplemented`. Phase 4 of the [_From Mock to Production_](https://www.ngx-ramblers.org.uk/how-to/technical-articles/2026-04-27-salesforce-mock-to-production) plan fills in the SOQL queries and field mappers.

## Architecture

- Node 20 + TypeScript (strict). No `.js` / `.mjs` / `.cjs` source files.
- Express + jsforce + pino + zod (request validation re-uses the schemas from the contract package).
- Single Salesforce org. Tenant boundary via `ALLOWED_GROUP_CODES` env var.
- Long-lived bearer tokens (sha256 hashes in `API_TOKEN_HASHES`).
- Deployed to Fly.io (`lhr`, app `ramblers-salesforce-server`).

## Local development

```sh
corepack enable                # one-off
pnpm install
cp .env.example .env           # fill in ALLOWED_GROUP_CODES + API_TOKEN_HASHES; SF_* optional
pnpm dev
```

`http://localhost:8080/healthz` returns `{status: "ok", uptime}`. `http://localhost:8080/healthz/salesforce` calls `conn.identity()` if the SF_* env vars are configured, or returns `503 NOT_CONFIGURED` otherwise.

## What Phase 4 needs to land

| File | Function | What HQ writes |
|---|---|---|
| `src/salesforce/connection.ts` | `buildJwtAssertion` | RS256-sign the JWT bearer assertion using the connected app's private key |
| `src/providers/salesforce-member-provider.ts` | `listMembers` | SOQL query + map records via `salesforceToMember` |
| `src/providers/salesforce-member-provider.ts` | `applyConsent` | composite request: update Contact + insert ConsentEvent__c |
| `src/providers/salesforce-member-provider.ts` | `salesforceToMember` | field mapping from typed Salesforce record → `SalesforceMember` |
| `src/providers/salesforce-member-provider.ts` | `memberToSalesforce` | reverse mapping for consent writeback |

The `MemberProvider` interface itself (and the `SalesforceMember` shape, the OpenAPI document, the Zod request schemas) all come from the contract package and must not be duplicated here.

## Deployment

`pnpm deploy` runs `flyctl deploy`. CI mirrors that on every push to `main`, gated by the `FLY_DEPLOY_ENABLED` repo variable so the workflow does not crash before the Fly app and `FLY_API_TOKEN` secret are set up.

Secrets (`API_TOKEN_HASHES`, `SF_CLIENT_ID`, `SF_USERNAME`, `SF_JWT_PRIVATE_KEY_PATH`) live in the NGX staging `config.environments` document — see the `connect-env-db` skill in the NGX-Ramblers repo for the lookup pattern.
