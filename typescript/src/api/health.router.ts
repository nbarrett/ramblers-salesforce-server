import { Router } from "express";
import type { Request, Response } from "express";
import { asyncHandler } from "./async-handler.js";
import { isSalesforceConfigured, loadConfig } from "../config.js";
import type { SalesforceConnection } from "../salesforce/connection.js";

export function createHealthRouter(salesforce: SalesforceConnection | undefined): Router {
  const router = Router();

  router.get("/healthz", (_req: Request, res: Response) => {
    res.status(200).json({
      status: "ok",
      uptime: Math.round(process.uptime()),
    });
  });

  router.get(
    "/healthz/salesforce",
    asyncHandler(async (_req: Request, res: Response) => {
      const config = loadConfig();
      if (!isSalesforceConfigured(config) || !salesforce) {
        res.status(503).json({
          status: "not_configured",
          message:
            "SF_CLIENT_ID, SF_USERNAME and SF_JWT_PRIVATE_KEY_PATH must be set for the Salesforce smoke test to run.",
        });
        return;
      }
      try {
        const identity = await salesforce.identity();
        res.status(200).json({ status: "ok", identity });
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        res.status(503).json({ status: "error", message });
      }
    }),
  );

  return router;
}
