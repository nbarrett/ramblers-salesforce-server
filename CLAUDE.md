# CLAUDE.md

## Critical Rules

1. **NEVER commit or push without explicit instruction** — make file changes freely; `git commit` and `git push` each need the user to explicitly ask.
2. **No code comments** — no `//`, no `/* */`, no JSDoc `/** */`. Self-documenting names.
3. **No AI attribution in commits** — `commit-msg` hook enforces.
4. **Strict TypeScript everywhere** — `.ts` only. No `.js` / `.mjs` / `.cjs` source files.
5. **Wire format comes from `@ramblers/sf-contract`** — never re-declare types, schemas, error envelopes, openapi shape or columns in this repo. Pin a `vX.Y.Z` tag in `package.json`. Bumping that tag is the *only* way wire-format changes flow into this server.
6. **DRY** — search `src/` first.

## Project Overview

- **Purpose**: production server for the Ramblers Salesforce API. Drop-in wire-format substitute for the mock at `salesforce-mock.ngx-ramblers.org.uk`. The Salesforce adapter is scaffolded; method bodies throw `NotImplemented` until Phase 4 (Ramblers HQ fill in SOQL queries and field mappers).
- **Architecture**: Node 20+, Express, jsforce, pino. Single Salesforce org. No database, no admin UI, no xlsx ingest, no synthetic data.
- **Repository**: https://github.com/nbarrett/ramblers-salesforce-server
- **Source**: `src/` (TypeScript only). `dist/server.js` is esbuild output.
- **Contract dep**: `@ramblers/sf-contract` from a pinned git tag — see [the contract repo](https://github.com/nbarrett/ramblers-salesforce-contract).

## Tenant model

One Salesforce org. `groupCode` from the URL path is validated against `ALLOWED_GROUP_CODES` (env-configured allow-list). Phase 4 may replace this with a Salesforce startup query.

## Auth

Long-lived bearer tokens. Each token's sha256 hash sits in `API_TOKEN_HASHES` (comma-separated env var). The server compares the incoming `Authorization: Bearer <token>` against the hash list. No per-tenant scoping at the token level — the org is the tenant boundary.

Not Auth0. Not OAuth (for *consumers* — Salesforce-side OAuth/JWT is a separate concern, used to authenticate this server *to* Salesforce).

## Code Style

- **Double quotes** always, never single
- **No "get" prefixes** on methods
- **`undefined` for absence**
- **`T[]` not `Array<T>`**
- **Immutable operations** — `map` / `reduce` / `filter`
- **kebab-case** for filenames
- **UK English** in commits, README, prose
- **Minimal changes** — patches scoped

## Bans

| Banned | Use instead |
|--------|------------|
| `console.log/warn/error` | `logger` from `src/logger.ts` |
| Inline comments | self-documenting code |
| `any` (without justification) | concrete types or `unknown` + narrowing |
| `^` / `~` ranges in `package.json` | pin every dependency to an exact version |
| `.js`, `.mjs`, `.cjs` source | `.ts` only |
| Re-declaring contract types here | import from `@ramblers/sf-contract` |

(Stylistic prose preferences live globally in `~/.claude/CLAUDE.md`.)

## Git Workflow

- **Conventional commits**: `<type>(<scope>): <description>`
- **Paragraph-style body** — root cause + supporting fixes
- **100% trunk-based on `main`** — no PRs, no branches, no worktrees
- **No literal `\n`** in commit messages
- **Hook setup**: `pnpm setup:hooks`. Hooks enforce no-AI-attribution on `commit-msg`, lint on `pre-commit`, typecheck/lint/test on `pre-push`

## Backend Patterns

- **Logger**: `import { logger } from "./logger.js"` (note `.js` — ESM compiled from TS)
- **Async route handlers**: wrap with `asyncHandler` from `src/api/async-handler.ts`
- **Validation**: Zod schemas from `@ramblers/sf-contract`; never trust unvalidated `req.body`
- **Errors**: `apiError(res, code, message, details?)` from `src/api/errors.ts`
- **OpenAPI**: served by the contract's `buildOpenApiDocument(options)` — runtime config injected at startup. Do not duplicate paths or schemas locally
- **Salesforce calls**: every Salesforce-side query lives in the `SalesforceMemberProvider` adapter. Routes only ever talk to the `MemberProvider` interface

## Phase 4 (HQ work)

- `src/providers/salesforce-member-provider.ts` — fill in `listMembers` and `applyConsent` bodies
- `src/providers/salesforce-member-provider.ts` — fill in `salesforceToMember` and `memberToSalesforce` field mappers
- `src/salesforce/connection.ts` — fill in `buildJwtAssertion` (RS256 signing of the JWT bearer flow)

## Commands

```bash
pnpm install                # corepack enable first if pnpm not yet active
pnpm dev                    # tsx watch on src/server.ts
pnpm build                  # esbuild → dist/server.js
pnpm start                  # run dist/server.js
pnpm typecheck              # tsc --noEmit on every .ts file
pnpm lint                   # eslint src/ scripts/
pnpm test                   # vitest run
pnpm setup:hooks            # one-off — activate .githooks/
pnpm deploy                 # flyctl deploy (Fly app: ramblers-salesforce-server, region: lhr)
```

## Mock vs Production

The same wire format is served by both servers. The two should be byte-identical from a consumer's perspective once Phase 4 is done. If you ever find yourself adding a route handler here that the mock does not have (or vice versa), that is a contract drift and the contract package should change first.
