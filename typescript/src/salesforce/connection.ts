import { Connection } from "jsforce";
import { readFile } from "node:fs/promises";
import type { AppConfig } from "../config.js";
import { isSalesforceConfigured } from "../config.js";
import { logger } from "../logger.js";

export interface SalesforceConnection {
  conn: Connection;
  identity(): Promise<{
    organisationId: string;
    userId: string;
    username: string;
    displayName: string;
  }>;
}

export async function createSalesforceConnection(
  config: AppConfig,
): Promise<SalesforceConnection | undefined> {
  if (!isSalesforceConfigured(config)) {
    logger.warn(
      "Salesforce credentials not configured - SalesforceMemberProvider will be unreachable. Set SF_CLIENT_ID, SF_USERNAME and SF_JWT_PRIVATE_KEY_PATH to enable.",
    );
    return undefined;
  }
  const privateKey = await readFile(config.SF_JWT_PRIVATE_KEY_PATH, "utf-8");
  const conn = new Connection({
    loginUrl: config.SF_LOGIN_URL,
    oauth2: {
      loginUrl: config.SF_LOGIN_URL,
      clientId: config.SF_CLIENT_ID,
    },
  });
  await conn.authorize({
    grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
    assertion: await buildJwtAssertion({
      audience: config.SF_LOGIN_URL,
      clientId: config.SF_CLIENT_ID,
      username: config.SF_USERNAME,
      privateKey,
    }),
  });
  return {
    conn,
    async identity() {
      const id = await conn.identity();
      return {
        organisationId: id.organization_id,
        userId: id.user_id,
        username: id.username,
        displayName: id.display_name,
      };
    },
  };
}

interface JwtAssertionOptions {
  audience: string;
  clientId: string;
  username: string;
  privateKey: string;
}

async function buildJwtAssertion(_options: JwtAssertionOptions): Promise<string> {
  throw new Error(
    "Phase 4: implement RS256 JWT assertion signing using SF_JWT_PRIVATE_KEY_PATH. Suggested: jsonwebtoken or jose. See https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm",
  );
}
