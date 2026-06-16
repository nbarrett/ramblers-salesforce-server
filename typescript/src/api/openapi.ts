import { buildOpenApiDocument } from "@ramblers/sf-contract";
import { loadConfig } from "../config.js";

let cached: Record<string, unknown> | undefined;

export function getOpenApiDocument(): Record<string, unknown> {
  if (cached) return cached;
  const config = loadConfig();
  cached = buildOpenApiDocument({
    publicBaseUrl: config.PUBLIC_BASE_URL,
    serverDescription: "Production deployment",
    info: {
      title: "Ramblers Salesforce API — Production Server",
      version: "0.1.0",
      description: [
        "## Status",
        "",
        "Phase 3 of the [_From Mock to Production_](https://www.ngx-ramblers.org.uk/how-to/technical-articles/2026-04-27-salesforce-mock-to-production) plan. The structural plumbing is in place; the Salesforce adapter is scaffolded but its method bodies are still pending. Authenticated requests currently return `501 NotImplemented` envelopes with structured hints about what Phase 4 fills in. `/healthz/salesforce` reports `503 not_configured` until Ramblers HQ wire the connected-app credentials.",
        "",
        "## Authentication",
        "",
        "Long-lived bearer tokens. Pass `Authorization: Bearer <token>` on every request. Tokens are issued per consumer (NGX-Ramblers, MailMan, etc.); the server compares the sha256 hash of the supplied token against `API_TOKEN_HASHES` (a comma-separated env var of allowed hashes). Click **Authorize** below to paste a token into Swagger UI before exercising the endpoints.",
        "",
        "## Tenant model",
        "",
        "One Salesforce org. The `groupCode` path parameter is validated against `ALLOWED_GROUP_CODES` (env-configured allow-list) on every request. Tokens carry no per-tenant scope; the org boundary is the tenant boundary.",
        "",
        "## Reference",
        "",
        "**→ [nbarrett/ngx-ramblers#209](https://github.com/nbarrett/ngx-ramblers/issues/209)** — day-one API contract this server implements.<br>",
        "**→ [@ramblers/sf-contract](https://github.com/nbarrett/ramblers-salesforce-contract)** — the wire-format package this server (and the mock) consume.<br>",
        "**→ [Mock server](https://salesforce-mock.ngx-ramblers.org.uk/docs)** — sibling deployment with synthetic data for consumer development and CI.<br>",
        "**→ [ramblers-salesforce-server on GitHub](https://github.com/nbarrett/ramblers-salesforce-server)** — this server's source.<br>",
        "**→ [Phase 4 checklist (#1)](https://github.com/nbarrett/ramblers-salesforce-server/issues/1)** — what Ramblers HQ fill in to switch the deployment from `501` to live data.<br>",
        "**→ [Raw openapi.json](/api/openapi.json)** — the document this page is rendered from.",
      ].join("\n"),
      contact: {
        name: "Ramblers Salesforce Server",
        url: "https://github.com/nbarrett/ramblers-salesforce-server",
      },
    },
  });
  return cached;
}
