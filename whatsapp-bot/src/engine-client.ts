import axios, { type AxiosInstance } from "axios";
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

const client: AxiosInstance = axios.create({
  baseURL: config.engineUrl,
  timeout: 60_000,
});

export async function moderateText(text: string): Promise<ModerationResult> {
  const { data } = await client.post<ModerationResult>("/moderate_text", {
    text,
  });
  return data;
}

export async function moderateImage(
  imageBytes: Buffer
): Promise<ModerationResult> {
  const { data } = await client.post<ModerationResult>("/moderate_image", {
    image_base64: imageBytes.toString("base64"),
  });
  return data;
}

export async function moderateVideo(
  videoBytes: Buffer
): Promise<ModerationResult> {
  const { data } = await client.post<ModerationResult>("/moderate_video", {
    video_base64: videoBytes.toString("base64"),
  });
  return data;
}
