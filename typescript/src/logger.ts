import pino from "pino";
import { loadConfig } from "./config.js";

const config = loadConfig();

export const logger = pino({
  level: config.LOG_LEVEL,
  base: { service: "ramblers-salesforce-server" },
});
