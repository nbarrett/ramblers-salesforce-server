import { createHash } from "node:crypto";
import type { NextFunction, Request, Response } from "express";
import { apiError } from "../api/errors.js";
import { loadConfig } from "../config.js";

declare global {
  namespace Express {
    interface Request {
      apiTokenHash?: string;
    }
  }
}

function extractBearerToken(authorizationHeader: string | undefined): string | undefined {
  if (!authorizationHeader) return undefined;
  const match = /^Bearer\s+(.+)$/i.exec(authorizationHeader);
  return match?.[1];
}

function hashToken(plaintext: string): string {
  return createHash("sha256").update(plaintext).digest("hex");
}

export function bearerAuth(req: Request, res: Response, next: NextFunction): void {
  const plaintext = extractBearerToken(req.header("authorization"));
  if (!plaintext) {
    apiError(res, "UNAUTHORIZED", "Missing or malformed Authorization header");
    return;
  }
  const incomingHash = hashToken(plaintext);
  const allowed = loadConfig().API_TOKEN_HASHES;
  if (allowed.length === 0) {
    apiError(
      res,
      "UNAUTHORIZED",
      "Server has no API_TOKEN_HASHES configured; all bearer requests rejected",
    );
    return;
  }
  if (!allowed.includes(incomingHash)) {
    apiError(res, "UNAUTHORIZED", "Unknown API token");
    return;
  }
  req.apiTokenHash = incomingHash;
  next();
}

export function requireGroupAllowed(groupCode: string, res: Response): boolean {
  const allowed = loadConfig().ALLOWED_GROUP_CODES;
  if (!allowed.includes(groupCode.toUpperCase())) {
    apiError(res, "GROUP_NOT_FOUND", `Group ${groupCode} is not in the configured allow-list`);
    return false;
  }
  return true;
}
