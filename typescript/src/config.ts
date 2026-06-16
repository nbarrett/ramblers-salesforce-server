import { z } from "zod";

const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().int().positive().default(8080),
  PUBLIC_BASE_URL: z.string().url().default("http://localhost:8080"),
  LOG_LEVEL: z.enum(["trace", "debug", "info", "warn", "error"]).default("info"),
  ALLOWED_GROUP_CODES: z
    .string()
    .default("")
    .transform((raw) =>
      raw
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter((s) => s.length > 0),
    ),
  API_TOKEN_HASHES: z
    .string()
    .default("")
    .transform((raw) =>
      raw
        .split(",")
        .map((s) => s.trim().toLowerCase())
        .filter((s) => s.length === 64),
    ),
  SF_LOGIN_URL: z.string().url().default("https://login.salesforce.com"),
  SF_CLIENT_ID: z.string().default(""),
  SF_USERNAME: z.string().default(""),
  SF_JWT_PRIVATE_KEY_PATH: z.string().default(""),
});

export type AppConfig = z.infer<typeof EnvSchema>;

let cached: AppConfig | undefined;

export function loadConfig(): AppConfig {
  if (cached) return cached;
  const parsed = EnvSchema.safeParse(process.env);
  if (!parsed.success) {
    const formatted = parsed.error.issues
      .map((i) => `  - ${i.path.join(".")}: ${i.message}`)
      .join("\n");
    throw new Error(`Invalid environment configuration:\n${formatted}`);
  }
  cached = parsed.data;
  return cached;
}

export function isSalesforceConfigured(config: AppConfig): boolean {
  return (
    config.SF_CLIENT_ID.length > 0 &&
    config.SF_USERNAME.length > 0 &&
    config.SF_JWT_PRIVATE_KEY_PATH.length > 0
  );
}
