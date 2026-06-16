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
pytest         # conformance + hybrid + end-to-end API tests (14)
```

`pytest` includes a conformance suite asserting the generated OpenAPI carries the v0.4.0 contract field names and value vocabularies, so this server cannot quietly diverge from the spec or the TypeScript sibling.
