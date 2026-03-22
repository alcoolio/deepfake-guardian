import axios, { type AxiosInstance, type AxiosError } from "axios";
import { config } from "./config";

export interface ModerationScores {
  violence: number;
  sexual_violence: number;
  nsfw: number;
  deepfake_suspect: number;
}

export interface ModerationResult {
  verdict: "allow" | "delete" | "flag";
  reasons: string[];
  scores: ModerationScores;
}

// ---------------------------------------------------------------------------
// Retry configuration
// ---------------------------------------------------------------------------
const MAX_RETRIES = 3;
const BACKOFF_FACTOR_MS = 1000; // 1s → 2s → 4s
const RETRY_STATUS_CODES = new Set([500, 502, 503, 504]);

// ---------------------------------------------------------------------------
// HTTP client
// ---------------------------------------------------------------------------
const headers: Record<string, string> = {};
if (config.engineApiKey) {
  headers["X-API-Key"] = config.engineApiKey;
}

const client: AxiosInstance = axios.create({
  baseURL: config.engineUrl,
  timeout: 60_000,
  headers,
});

// ---------------------------------------------------------------------------
// Retry helper
// ---------------------------------------------------------------------------
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function postWithRetry<T>(path: string, data: unknown): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const { data: responseData } = await client.post<T>(path, data);
      return responseData;
    } catch (err) {
      const axiosErr = err as AxiosError;
      const isRetryable =
        !axiosErr.response || RETRY_STATUS_CODES.has(axiosErr.response.status);

      lastError = axiosErr;

      if (isRetryable && attempt < MAX_RETRIES) {
        const waitMs = BACKOFF_FACTOR_MS * Math.pow(2, attempt);
        console.warn(
          `[engine-client] Request to ${path} failed (attempt ${attempt + 1}/${MAX_RETRIES + 1}), retrying in ${waitMs}ms — ${axiosErr.message}`
        );
        await sleep(waitMs);
      } else {
        break;
      }
    }
  }

  throw lastError;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------
export async function moderateText(text: string): Promise<ModerationResult> {
  return postWithRetry<ModerationResult>("/moderate_text", { text });
}

export async function moderateImage(
  imageBytes: Buffer
): Promise<ModerationResult> {
  return postWithRetry<ModerationResult>("/moderate_image", {
    image_base64: imageBytes.toString("base64"),
  });
}

export async function moderateVideo(
  videoBytes: Buffer
): Promise<ModerationResult> {
  return postWithRetry<ModerationResult>("/moderate_video", {
    video_base64: videoBytes.toString("base64"),
  });
}
