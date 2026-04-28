import { Router } from "express";
import type { Request, Response } from "express";
import {
  consentUpdateRequestSchema,
  listMembersQuerySchema,
  type ConsentUpdateRequest,
  type MemberProvider,
} from "@ramblers/sf-contract";
import { bearerAuth, requireGroupAllowed } from "../auth/bearer-auth.js";
import { apiError } from "./errors.js";
import { asyncHandler } from "./async-handler.js";
import { NotImplemented } from "../providers/salesforce-member-provider.js";
import { logger } from "../logger.js";

export function createApiRouter(provider: MemberProvider): Router {
  const router = Router();

  router.get(
    "/api/groups/:groupCode/members",
    bearerAuth,
    asyncHandler(async (req: Request, res: Response) => {
      const groupCode = req.params["groupCode"];
      if (!groupCode) {
        apiError(res, "BAD_REQUEST", "groupCode path parameter is required");
        return;
      }
      if (!requireGroupAllowed(groupCode, res)) return;

      const parsed = listMembersQuerySchema.safeParse(req.query);
      if (!parsed.success) {
        apiError(res, "BAD_REQUEST", "Invalid query parameters", {
          issues: parsed.error.issues,
        });
        return;
      }
      const { since, includeExpired } = parsed.data;

      try {
        const result = await provider.listMembers({
          groupCode,
          ...(since ? { since: new Date(since) } : {}),
          ...(includeExpired !== undefined ? { includeExpired } : {}),
        });

        if (result.kind === "groupNotFound") {
          apiError(res, "GROUP_NOT_FOUND", `No data for ${groupCode}`);
          return;
        }
        res.json(result.response);
      } catch (err: unknown) {
        if (err instanceof NotImplemented) {
          logger.warn({ symbol: err.message, notes: err.notes }, "501 NotImplemented");
          apiError(
            res,
            "INTERNAL_ERROR",
            "listMembers is not implemented in this server yet (Phase 4)",
            { hint: err.notes },
          );
          res.status(501);
          return;
        }
        throw err;
      }
    }),
  );

  router.post(
    "/api/members/:membershipNumber/consent",
    bearerAuth,
    asyncHandler(async (req: Request, res: Response) => {
      const membershipNumber = req.params["membershipNumber"];
      if (!membershipNumber) {
        apiError(res, "BAD_REQUEST", "membershipNumber path parameter is required");
        return;
      }
      const parsed = consentUpdateRequestSchema.safeParse(req.body);
      if (!parsed.success) {
        apiError(res, "BAD_REQUEST", "Invalid consent request body", {
          issues: parsed.error.issues,
        });
        return;
      }
      const body = parsed.data;
      const consentRequest: ConsentUpdateRequest = {
        source: body.source,
        timestamp: body.timestamp,
        ...(body.emailMarketingConsent !== undefined
          ? { emailMarketingConsent: body.emailMarketingConsent }
          : {}),
        ...(body.groupMarketingConsent !== undefined
          ? { groupMarketingConsent: body.groupMarketingConsent }
          : {}),
        ...(body.areaMarketingConsent !== undefined
          ? { areaMarketingConsent: body.areaMarketingConsent }
          : {}),
        ...(body.otherMarketingConsent !== undefined
          ? { otherMarketingConsent: body.otherMarketingConsent }
          : {}),
        ...(body.reason !== undefined ? { reason: body.reason } : {}),
      };
      try {
        const result = await provider.applyConsent({
          tenantCode: "PRODUCTION",
          membershipNumber,
          request: consentRequest,
          appliedAt: new Date(),
        });
        if (result.kind === "memberNotFound") {
          apiError(
            res,
            "MEMBER_NOT_FOUND",
            `No member with membershipNumber ${membershipNumber}`,
          );
          return;
        }
        res.status(200).json(result.response);
      } catch (err: unknown) {
        if (err instanceof NotImplemented) {
          logger.warn({ symbol: err.message, notes: err.notes }, "501 NotImplemented");
          apiError(
            res,
            "INTERNAL_ERROR",
            "applyConsent is not implemented in this server yet (Phase 4)",
            { hint: err.notes },
          );
          res.status(501);
          return;
        }
        throw err;
      }
    }),
  );

  return router;
}
