"use client";

import { authResponseSchema, getToken } from "./auth";
import type {
  Artist,
  ArtistListResponse,
  AuthBody,
  CreateArtistBody,
  CreateTrackBody,
  HealthResponse,
  JobEventsResponse,
  PublicKaraokeDocument,
  PublicKaraokeManifest,
  Publication,
  RegisterBody,
  ReviewEventsResponse,
  ReviewQueueResponse,
  ReviewQueueStatus,
  StartTranscriptionResponse,
  Track,
  TrackListResponse,
  TrackVersion,
  TranscriptionJob,
  TranscriptDocument,
  UploadCompleteBody,
  UploadUrl,
  UploadUrlBody,
} from "./types";

type RequestMethod = "GET" | "POST" | "PATCH";

type RequestOptions = {
  method?: RequestMethod;
  body?: unknown;
  auth?: boolean;
  signal?: AbortSignal;
};

export class ApiClient {
  auth = {
    login: async (body: AuthBody) =>
      authResponseSchema.parse(
        await this.request<unknown>("/api/auth/login", { method: "POST", body }),
      ),
    register: async (body: RegisterBody) =>
      authResponseSchema.parse(
        await this.request<unknown>("/api/auth/register", { method: "POST", body }),
      ),
  };

  artists = {
    list: () => this.request<ArtistListResponse>("/api/artists"),
    create: (body: CreateArtistBody) =>
      this.request<Artist>("/api/artists", { method: "POST", auth: true, body }),
  };

  tracks = {
    list: () => this.request<TrackListResponse>("/api/tracks"),
    get: (trackId: string) => this.request<Track>(`/api/tracks/${trackId}`),
    create: (body: CreateTrackBody) =>
      this.request<Track>("/api/tracks", { method: "POST", auth: true, body }),
    versions: (trackId: string) => this.request<TrackVersion[]>(`/api/tracks/${trackId}/versions`),
    createVersion: (trackId: string) =>
      this.request<TrackVersion>(`/api/tracks/${trackId}/versions`, {
        method: "POST",
        auth: true,
        body: {},
      }),
  };

  versions = {
    get: (versionId: string) =>
      this.request<TrackVersion>(`/api/versions/${versionId}`, { auth: true }),
    uploadUrl: (versionId: string, body: UploadUrlBody) =>
      this.request<UploadUrl>(`/api/versions/${versionId}/upload-url`, {
        method: "POST",
        auth: true,
        body,
      }),
    uploadComplete: (versionId: string, body: UploadCompleteBody) =>
      this.request<TrackVersion>(`/api/versions/${versionId}/upload-complete`, {
        method: "POST",
        auth: true,
        body,
      }),
    startTranscription: (versionId: string) =>
      this.request<StartTranscriptionResponse>(`/api/versions/${versionId}/start-transcription`, {
        method: "POST",
        auth: true,
        body: {},
      }),
    transcript: (versionId: string) =>
      this.request<TranscriptDocument>(`/api/versions/${versionId}/transcript`, { auth: true }),
    reviewEvents: (versionId: string) =>
      this.request<ReviewEventsResponse>(`/api/versions/${versionId}/review-events`, {
        auth: true,
      }),
    approve: (versionId: string, note?: string) =>
      this.request<TrackVersion>(`/api/versions/${versionId}/approve`, {
        method: "POST",
        auth: true,
        body: { note: note || null },
      }),
    reject: (versionId: string, reason: string) =>
      this.request<TrackVersion>(`/api/versions/${versionId}/reject`, {
        method: "POST",
        auth: true,
        body: { reason },
      }),
    publish: (versionId: string) =>
      this.request<Publication>(`/api/versions/${versionId}/publish`, {
        method: "POST",
        auth: true,
        body: { make_latest: true },
      }),
  };

  publicKaraoke = {
    manifest: (artistSlug: string, trackSlug: string) =>
      this.request<PublicKaraokeManifest>(
        `/api/public/karaoke/${artistSlug}/${trackSlug}/manifest`,
      ),
    latest: (artistSlug: string, trackSlug: string) =>
      this.request<PublicKaraokeDocument>(
        `/api/public/karaoke/${artistSlug}/${trackSlug}/latest`,
      ),
    version: (artistSlug: string, trackSlug: string, version: number) =>
      this.request<PublicKaraokeDocument>(
        `/api/public/karaoke/${artistSlug}/${trackSlug}/versions/${version}`,
      ),
  };

  review = {
    queue: (status: ReviewQueueStatus, limit = 20, offset = 0) =>
      this.request<ReviewQueueResponse>(
        `/api/review/queue?status=${status}&limit=${limit}&offset=${offset}`,
        { auth: true },
      ),
  };

  jobs = {
    get: (jobId: string) => this.request<TranscriptionJob>(`/api/jobs/${jobId}`, { auth: true }),
    events: (jobId: string) =>
      this.request<JobEventsResponse>(`/api/jobs/${jobId}/events`, { auth: true }),
  };

  health = (options: Omit<RequestOptions, "method" | "body" | "auth"> = {}) =>
    this.request<HealthResponse>("/api/health", options);

  private async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const headers = new Headers();

    if (options.body !== undefined) {
      headers.set("Content-Type", "application/json");
    }

    if (options.auth) {
      const token = getToken();

      if (token) {
        headers.set("Authorization", `Bearer ${token}`);
      }
    }

    const response = await fetch(path, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Request failed with ${response.status}`);
    }

    return (await response.json()) as T;
  }
}
