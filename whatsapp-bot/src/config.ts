import "dotenv/config";

export const config = {
  engineUrl: process.env.ENGINE_URL ?? "http://localhost:8000",
  engineApiKey: process.env.ENGINE_API_KEY ?? "",
  sessionDataPath: process.env.SESSION_DATA_PATH ?? "./auth_info",
  logLevel: process.env.LOG_LEVEL ?? "info",
} as const;
