# ramblers-salesforce-server

Language-agnostic home for the Ramblers Salesforce member API server ([ngx-ramblers#209](https://github.com/nbarrett/ngx-ramblers/issues/209)). Two reference implementations of the same wire contract (`@ramblers/sf-contract` v0.4.0) live side by side and are byte-identical from a consumer's point of view.

| Directory | Stack | Deploy target | Role |
|---|---|---|---|
| [`typescript/`](typescript/) | Express + jsforce (Node 20) | Fly.io | Original production reference |
| [`python/`](python/) | FastAPI (Python 3.11) | Azure Container Apps | Offered to Ramblers HQ for their Python / Azure / Entra stack; **live** |

Both consume `@ramblers/sf-contract` for the wire format and leave the Salesforce queries as Phase 4 work for the data owner.

## This repo's servers vs the mock

Worth keeping straight, because they answer different questions:

- **The servers in this repo** are the real thing - in production they read from Salesforce.
- The separate [**mock**](https://github.com/nbarrett/ramblers-salesforce-mock) is a standalone *fake of the API* (Mongo-backed, with an admin console, synthetic data and lifecycle scenarios) that consumers (NGX, MailMan) point their own clients at for integration testing. The servers never consume it.

## Operating modes

The **Python server** runs in either of two modes, chosen by `PROVIDER`:

- **Demo** (`PROVIDER=demo`, default) - serves deterministic synthetic data with no Salesforce, no database and no auth. This is the *actual production server run cold*: clone it and watch the real routing, validation, OpenAPI and hybrid-overlay code work in seconds. Live now at [salesforce-server.ngx-ramblers.org.uk](https://salesforce-server.ngx-ramblers.org.uk).
- **Production** (`PROVIDER=salesforce`) - the same server reading from Salesforce, with an overlay store for the fields Salesforce charges to hold. The data owner fills in three methods (Phase 4).

The **TypeScript server** is the original production reference: it reads from Salesforce, with its adapter stubbed until Phase 4. It deliberately does *not* carry its own synthetic data - to see the API work with sample data, run the mock or the Python server's demo mode. That keeps demo data the mock's job and this server's job purely production.

Each directory's `README.md` gives the exact configuration for each mode.

## Deploying

- **Python → Azure Container Apps** is the default. A push to `main` has GitHub Actions build the image on the runner, push it to the container registry and update the Container App. Active once the `AZURE_DEPLOY_ENABLED` variable and the `AZURE_CREDENTIALS` secret are set.
- **TypeScript → Fly.io** deploys on demand (run the "Deploy" workflow with target `typescript`). Active once `FLY_DEPLOY_ENABLED` and `FLY_API_TOKEN` are set.

Repo-root `.githooks` enforce the no-AI-attribution and lint rules across both stacks; CI runs the full check suite for each on every PR.
