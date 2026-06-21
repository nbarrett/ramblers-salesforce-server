# Configuration & secrets

Everything the server reads from the environment, what each setting is for, and which are secrets. The aim is that a new operator (Ramblers HQ) can stand the server up in their own infrastructure and know exactly what to set, what is sensitive, and where each value comes from.

Nothing here is host-specific: the server runs the same way on Azure Container Apps (where the reference deployment lives), any container host, or a plain VM. The reference deployment's wiring is in [`infra/`](infra/).

## Two modes

The server has one job: serve the member API in the contract wire shape. It runs in one of two modes, set by `PROVIDER`:

- **Demo** (`PROVIDER=demo`) - synthetic data, no Salesforce, no database, no auth. Nothing below is required; the server runs cold. This is what the public demo runs.
- **Production** (`PROVIDER=salesforce`) - reads from Salesforce, with an Azure Table overlay for the extension fields. Requires the Salesforce, auth and overlay settings below.

## Settings

| Variable | Required when | Secret | Purpose | Example / format |
|---|---|---|---|---|
| `PROVIDER` | always (defaults to `demo`) | no | `demo` (synthetic) or `salesforce` (real source + overlay) | `salesforce` |
| `AUTH_MODE` | always (defaults to `none`) | no | `none` (open), `entra` (validate Entra JWTs), `token` (hashed bearer) | `entra` |
| `ALLOWED_GROUP_CODES` | production | no | Comma-separated group/area codes this deployment serves | `KT50,EK,SE12` |
| `PUBLIC_BASE_URL` | never (defaults to `/`) | no | Server URL advertised in the OpenAPI document. Leave unset - the default `/` makes `/docs` call whatever host serves it | `/` |
| `DEMO_GROUP_CODE` | demo only | no | The group the demo generates | `KT50` |
| **Entra auth** (`AUTH_MODE=entra`) | | | | |
| `ENTRA_TENANT_ID` | entra mode | no (public identifier) | The Entra tenant (directory) id whose tokens are accepted | `00000000-0000-0000-0000-000000000000` |
| `ENTRA_AUDIENCE` | entra mode | no (public identifier) | The API app registration's Application (client) id - the `aud` the server requires | `00000000-0000-0000-0000-000000000000` |
| **Token auth** (`AUTH_MODE=token`) | | | | |
| `API_TOKEN_HASHES` | token mode | **yes** (the hashes) | Comma-separated sha256 hashes of the bearer tokens issued to consumers | `9f86d0818...,2c26b46b6...` |
| **Overlay store** | | | | |
| `OVERLAY_CONNECTION_STRING` | production | **yes** | Azure Storage connection string for the consent/extension overlay table. Unset falls back to in-memory (demo only) | `DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...` |
| `OVERLAY_TABLE_NAME` | optional | no | Overlay table name | `memberoverlay` |
| **Salesforce connection** (Phase 4) | | | | |
| Salesforce login URL, connected-app consumer key, integration username, and the JWT private key | production, once Phase 4 is implemented | key is **yes** | Authenticate the server to Salesforce (JWT bearer flow). These settings are added when the Salesforce source is implemented - see issue #3. The private key belongs in Key Vault (`sf-jwt-private-key`). | - |

## The secrets

Only three things are genuinely sensitive. Store them in a secret manager (the reference deployment uses Azure Key Vault, read by the Container App's managed identity - see [`infra/keyvault-setup.sh`](infra/keyvault-setup.sh)). Never put them in source control, a plain environment variable in a committed file, or a log.

| Secret | What it is | How to obtain / rotate | Notes |
|---|---|---|---|
| `OVERLAY_CONNECTION_STRING` | Azure Storage connection string for the overlay table; carries the storage account key | `az storage account keys list` (rotate by regenerating the key) | Only needed in production, or to persist the overlay in demo. Regenerable. |
| Salesforce JWT private key | The connected app's RSA private key (PEM) the server signs its Salesforce auth assertion with | Generated when HQ create the Salesforce connected app | Phase 4. Hold in Key Vault as `sf-jwt-private-key`. |
| Consumer client secrets | Each **consumer** (NGX-Ramblers, MailMan) holds its own Entra app secret to fetch tokens | `az ad app credential reset --id <consumer-app-id>` | Consumer-side, not server config. The server never holds these - it only validates the resulting JWTs. |

Note what is **not** a secret: `ENTRA_TENANT_ID` and `ENTRA_AUDIENCE` are public identifiers that appear in every issued token. They are configuration, not secrets, and belong in your IaC.

## Entra (when `AUTH_MODE=entra`)

The server validates inbound Microsoft Entra ID access tokens (RS256) against the tenant JWKS, checking issuer and audience. Set up the app registrations with [`infra/entra-setup.sh`](infra/entra-setup.sh), which creates:

- an **API** app registration (the resource; its Application id is `ENTRA_AUDIENCE`),
- a **consumer** app registration per consumer, with a client secret and the `members.read` app role.

A consumer fetches a token by the client-credentials flow and sends it as `Authorization: Bearer <token>`. The server's only inputs are `ENTRA_TENANT_ID` and `ENTRA_AUDIENCE`; the single validation seam is `_verify_entra` in [`app/auth.py`](app/auth.py).

## Handover template

The full set to hand to a new operator. Fill the right-hand side with your own infrastructure's values; keep the secrets in your secret manager, not in this file.

```bash
# --- Non-secret configuration (safe in IaC / plain env) ---
PROVIDER=salesforce
AUTH_MODE=entra
ALLOWED_GROUP_CODES=<your group/area codes, comma-separated>
ENTRA_TENANT_ID=<your Entra tenant (directory) id>
ENTRA_AUDIENCE=<your API app registration's Application (client) id>
OVERLAY_TABLE_NAME=memberoverlay
# PUBLIC_BASE_URL is optional; leave unset (defaults to "/")

# --- Secrets (store in Key Vault / your secret manager, never in source) ---
OVERLAY_CONNECTION_STRING=<Azure Storage connection string for the overlay table>
# Phase 4 (Salesforce), added when the Salesforce source is implemented (issue #3):
#   SF login URL, connected-app consumer key, integration username
#   sf-jwt-private-key  -> the connected-app private key PEM, in Key Vault

# --- Each consumer (NGX-Ramblers, MailMan) holds its own, not the server ---
#   <consumer-app-id> + <consumer-client-secret>  -> fetch tokens by client-credentials
```
