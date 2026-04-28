import express from "express";
import type { Request, Response } from "express";
import pinoHttp from "pino-http";
import swaggerUi from "swagger-ui-express";
import { loadConfig } from "./config.js";
import { logger } from "./logger.js";
import { createApiRouter } from "./api/members.router.js";
import { createHealthRouter } from "./api/health.router.js";
import { getOpenApiDocument } from "./api/openapi.js";
import { SalesforceMemberProvider } from "./providers/salesforce-member-provider.js";
import { createSalesforceConnection, type SalesforceConnection } from "./salesforce/connection.js";

const config = loadConfig();

export async function createApp(): Promise<express.Express> {
  const app = express();

  app.disable("x-powered-by");
  app.set("trust proxy", 1);

  app.use(pinoHttp({ logger }));
  app.use(express.json({ limit: "512kb" }));

  let salesforce: SalesforceConnection | undefined;
  try {
    salesforce = await createSalesforceConnection(config);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    logger.error(
      { err: message },
      "Failed to initialise Salesforce connection - server starts anyway, /healthz/salesforce will report the failure.",
    );
  }

  app.use(createHealthRouter(salesforce));

  const openapi = getOpenApiDocument();
  app.get("/api/openapi.json", (_req: Request, res: Response) => {
    res.json(openapi);
  });
  app.use(
    "/docs",
    swaggerUi.serve,
    swaggerUi.setup(openapi, {
      customSiteTitle: "Ramblers Salesforce API - Production Server",
      swaggerOptions: { persistAuthorization: true },
    }),
  );

  if (!salesforce) {
    logger.warn(
      "Mounting members.router without a Salesforce connection - every call will throw NotImplemented or fail at the connection layer.",
    );
  }
  const provider = new SalesforceMemberProvider(
    salesforce ?? ({ conn: undefined as unknown, identity: async () => { throw new Error("No Salesforce connection"); } } as unknown as SalesforceConnection),
  );
  app.use(createApiRouter(provider));

  app.get("/", (_req: Request, res: Response) => {
    res.redirect("/docs");
  });

  return app;
}

async function main(): Promise<void> {
  const app = await createApp();
  app.listen(config.PORT, () => {
    logger.info(
      { port: config.PORT, baseUrl: config.PUBLIC_BASE_URL },
      "ramblers-salesforce-server listening",
    );
  });
}

const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  main().catch((err: unknown) => {
    logger.error({ err }, "fatal bootstrap error");
    process.exit(1);
  });
}
