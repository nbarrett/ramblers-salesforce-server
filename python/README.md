# Python implementation (FastAPI / Azure Container Apps)

Reference implementation of the Ramblers Salesforce member API for the Python / Azure / Entra stack. It's the `python/` half of the `ramblers-salesforce-server` repo, a sibling of the [TypeScript server](../typescript); both serve the same wire contract (`@ramblers/sf-contract` v0.4.0) and are interchangeable to a consumer.

## Run it in 30 seconds

```bash
cd python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 7071
```

Then:
- **http://localhost:7071/docs** - the whole API, live, with Swagger UI.
- `curl localhost:7071/api/groups/KT50/members` - 20 real members. No Salesforce, no database, no config.
- `curl -X POST localhost:7071/api/members/KT50-1000/consent -H 'content-type: application/json' -d '{"groupMarketingConsent": true, "source": "ngx-ramblers", "timestamp": "2026-06-16T00:00:00Z"}'`

It starts in **demo mode**: synthetic data behind the real server. Everything you're looking at - routing, validation, the generated OpenAPI, the error envelope, the auth layer - is the production code. The only thing not wired to Salesforce is the data source.

## The shape of it

Everything goes through one seam, the contract's `MemberProvider` port:

```
routes ──▶ MemberProvider (the contract's port)
              └─ HybridMemberProvider
                   ├─ MemberSource   ← Salesforce-native fields   (SalesforceMemberSource | SyntheticMemberSource)
                   └─ OverlayStore   ← fields Salesforce charges for (AzureTableOverlayStore | InMemoryOverlayStore)
```

### Hybrid persistence - the answer to "Salesforce is expensive about custom data"

Salesforce charges for custom fields. So the attributes it won't hold cheaply - `preferredName`, the granular group / area / other marketing-consent flags - live in a cheap **overlay store** (Azure Table Storage), keyed by `salesforceId`. `HybridMemberProvider` merges them on top of the Salesforce-native fields, so consumers still get one member in the exact contract shape and never know where any field physically lives.

The rules that keep it sane:
- **One home per attribute.** A field is either in Salesforce or in the overlay, never both. A manifest (`app/overlay/store.py`) lists what the overlay owns.
- **Permanent hybrid is fine.** Fields can live in the overlay for good. If HQ ever wants to promote one into Salesforce, backfill it and drop it from the manifest - the API contract never changes, so no consumer breaks.
- **GDPR:** the overlay holds member consent data, so deploy the storage account in a UK region (it's encrypted at rest) and use `OverlayStore.delete` for erasure.

## What you implement (Phase 4)

Three methods in `app/sources/salesforce.py`:

| Method | Does |
|---|---|
| `list_members` | SOQL for a group's Contacts, mapped to `SalesforceMember` (native fields only) |
| `find` | one member by membership number |
| `set_email_consent` | write the native `emailMarketingConsent` field |

That's the whole job. The overlay, the merge, the routing, the validation, the OpenAPI, the auth and the error handling are done. Set `PROVIDER=salesforce` and fill those in.

## Operating modes

Chosen by `PROVIDER`:

- **Demo** (`PROVIDER=demo`, the default) - synthetic data, no Salesforce, no database, no auth. The whole server runs; only the data source is fake. This is what's deployed at the live URL, so anyone can clone it and see it work. (Demo data for *consumer* integration testing is a separate concern - that's the [mock server](https://github.com/nbarrett/ramblers-salesforce-mock), a standalone fake of the API this server never consumes.)
- **Production** (`PROVIDER=salesforce`) - reads from Salesforce, with the Azure Table overlay for the extension fields. Fill in the three Phase 4 methods and set the Salesforce + Entra configuration below.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PROVIDER` | `demo` | `demo` (synthetic + in-memory overlay) or `salesforce` (real source + Azure Table overlay) |
| `AUTH_MODE` | `none` | `none` (demo), `entra` (validate Entra JWTs), or `token` (hashed bearer, parity with the mock) |
| `DEMO_GROUP_CODE` | `KT50` | the group the demo generates |
| `ENTRA_TENANT_ID` / `ENTRA_AUDIENCE` | - | required for `AUTH_MODE=entra` |
| `OVERLAY_CONNECTION_STRING` | - | Azure Storage connection string for the overlay (falls back to in-memory if unset) |
| `ALLOWED_GROUP_CODES` | - | per-deployment group/area allow-list |

## Authentication

Inbound auth is chosen by `AUTH_MODE`, and the bearer scheme is declared to OpenAPI - so the Swagger UI at `/docs` always shows an **Authorize** button (matching the mock), whatever the mode:

| `AUTH_MODE` | What it does |
|---|---|
| `none` (default) | Not enforced. The deployed demo runs here, so the live endpoints are open. The Authorize button still appears, to show consumers the production shape. |
| `entra` | Validates a Microsoft **Entra ID** access token (JWT, RS256) against the tenant JWKS, checking issuer and audience. This is the app-to-app (OAuth2 client-credentials) shape Ramblers HQ run. |
| `token` | sha256s an opaque bearer against the `API_TOKEN_HASHES` allow-list, for parity with the mock / TypeScript server. |

### Plugging in Entra

Entra is the production default for HQ, and switching it on is configuration, not code - **nothing in the routes changes**:

1. In your Entra tenant, register an **API** app: expose it as `api://<api-app-id>`, and set its access-token version to v2.0 (so the issuer is `https://login.microsoftonline.com/<tenant>/v2.0`, which is what the server checks).
2. Register a **consumer** app (one per consumer, e.g. NGX-Ramblers, MailMan) with a client secret, and grant it an application role on the API.
3. Point the server at Entra:

   ```bash
   AUTH_MODE=entra
   ENTRA_TENANT_ID=<your-tenant-id>
   ENTRA_AUDIENCE=<the API app id>   # the aud claim the server requires
   ```

A consumer then fetches a token by client-credentials and calls the API with `Authorization: Bearer <token>`:

```bash
curl -X POST https://login.microsoftonline.com/<tenant>/oauth2/v2.0/token \
  -d grant_type=client_credentials -d client_id=<consumer-app-id> \
  --data-urlencode client_secret=<secret> \
  --data-urlencode scope=api://<api-app-id>/.default
# -> paste the returned access_token into the /docs Authorize box, or send it as a Bearer header
```

The single code seam is `_verify_entra` in [`app/auth.py`](app/auth.py); the only inputs HQ supply are the tenant id and the audience. On a Container App the two settings can be left in place permanently while `AUTH_MODE=none` (they are inert), so a deployment flips between open demo and enforced Entra by changing that one variable.

## Deploy to Azure

The server runs on **Azure Container Apps**, live at [salesforce-server.ngx-ramblers.org.uk](https://salesforce-server.ngx-ramblers.org.uk). A push to `main` has GitHub Actions build the image on the runner, push it to the container registry, and update the Container App (needs the `AZURE_DEPLOY_ENABLED` variable and the `AZURE_CREDENTIALS` secret).

To provision Azure from scratch (after `az login`):

```bash
bash infra/azure-setup.sh ramblers-sf-py uksouth
```

The same FastAPI app also runs unchanged on the **Azure Functions** Python v2 model (`function_app.py`, `host.json`, the Bicep are kept for any Azure that has the Functions quota).

## Tests

```bash
ruff check .   # lint
mypy app       # types (strict)
pytest         # conformance + hybrid + end-to-end API tests (15)
```

`pytest` includes a conformance suite asserting the generated OpenAPI carries the v0.4.0 contract field names and value vocabularies, so this server cannot quietly diverge from the spec or the TypeScript sibling.
