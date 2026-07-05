export type User = {
  id: string;
  email: string;
  username: string;
  role: "user" | "reviewer" | "admin";
};

export type Artist = {
  id: string;
  slug: string;
  display_name: string;
  full_name: string | null;
};

export type Track = {
  id: string;
  artist_id: string;
  title: string;
  album: string | null;
  slug: string;
  artist?: {
    id: string;
    slug: string;
    display_name: string;
  } | null;
};

export type TrackVersion = {
  id: string;
  track_id: string;
  version: number;
  status:
    | "draft"
    | "upload_url_created"
    | "uploaded"
    | "queued_for_processing"
    | "processing"
    | "completed"
    | "failed"
    | "approved"
    | "rejected"
    | "published";
  temporary_audio_object_key: string | null;
  original_audio_filename: string | null;
  audio_content_type: string | null;
  audio_size_bytes: number | null;
  transcript_object_key?: string | null;
  manifest_object_key?: string | null;
  transcript_sha256?: string | null;
  transcript_schema_version?: string | null;
  duration_seconds?: number | null;
  word_count?: number | null;
  approved_at?: string | null;
  approved_by_user_id?: string | null;
  rejected_at?: string | null;
  rejected_by_user_id?: string | null;
  rejection_reason?: string | null;
};

export type UploadUrl = {
  upload_url: string;
  method: "PUT";
  object_key: string;
  expires_in_seconds: number;
  headers: Record<string, string>;
};

export type StartTranscriptionResponse = {
  job_id: string;
  track_version_id: string;
  status: "queued";
  correlation_id: string;
};

export type TranscriptionJob = {
  id: string;
  track_version_id: string;
  status: "queued" | "started" | "processing" | "completed" | "failed" | "cancelled";
  engine: string;
  progress: number;
  error_code: string | null;
  error_message: string | null;
  correlation_id: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type JobEvent = {
  event_id: string;
  event_type: string;
  created_at: string;
  payload: Record<string, unknown>;
};

export type JobEventsResponse = {
  job_id: string;
  events: JobEvent[];
};

export type ReviewQueueStatus = "completed" | "approved" | "rejected" | "failed";

export type ReviewQueueItem = {
  version_id: string;
  track_id: string;
  artist: {
    id: string;
    slug: string;
    display_name: string;
  };
  track: {
    id: string;
    title: string;
    slug: string;
    album: string | null;
  };
  version: number;
  status: TrackVersion["status"];
  job: {
    id: string;
    status: TranscriptionJob["status"];
    completed_at: string | null;
  } | null;
  summary: {
    duration_seconds: number | null;
    word_count: number | null;
    engine: string | null;
  };
  created_at: string;
  updated_at: string;
};

export type ReviewQueueResponse = {
  items: ReviewQueueItem[];
  limit: number;
  offset: number;
  total: number;
};

export type TranscriptWord = {
  word: string;
  start: number;
  end: number;
  confidence?: number | null;
};

export type TranscriptSegment = {
  id: number | string;
  start: number;
  end: number;
  text: string;
  words: TranscriptWord[];
};

export type TranscriptDocument = {
  schema_version: string;
  track?: {
    artist: string;
    album?: string | null;
    title: string;
    version: number;
  };
  track_version_id?: string | null;
  job_id?: string | null;
  engine: {
    name: string;
    model?: string | null;
    language?: string | null;
  };
  metadata: {
    duration_seconds?: number | null;
    created_at?: string | null;
    word_count?: number | null;
    segment_count?: number | null;
  };
  text?: string | null;
  segments: TranscriptSegment[];
};

export type Publication = {
  id: string;
  track_id: string;
  track_version_id: string;
  version: number;
  status: "published" | "unpublished" | "superseded";
  public_manifest_object_key: string;
  public_latest_object_key: string | null;
  public_transcript_object_key: string;
  public_segments_object_key: string | null;
  public_words_object_key: string | null;
  public_urls: {
    manifest: string;
    latest: string | null;
    version: string;
  };
  published_by_user_id: string | null;
  published_at: string | null;
  unpublished_at: string | null;
  created_at: string;
  updated_at: string;
};

export type PublicKaraokeManifest = {
  schema_version: string;
  artist: {
    id: string;
    slug: string;
    display_name: string;
  };
  track: {
    id: string;
    title: string;
    slug: string;
    album: string | null;
  };
  latest_version: number | null;
  versions: Array<{
    version: number;
    publication_id: string;
    status: Publication["status"];
    published_at: string | null;
    manifest_url: string;
    transcript_url: string;
  }>;
};

export type PublicKaraokeDocument = {
  manifest: PublicKaraokeManifest;
  transcript: TranscriptDocument;
};

export type ReviewEvent = {
  id: string;
  action: "approved" | "rejected" | "commented";
  reason: string | null;
  reviewer: {
    id: string;
    username: string;
  };
  created_at: string;
};

export type ReviewEventsResponse = {
  items: ReviewEvent[];
};

export type HealthResponse = {
  status: "ok";
  service: string;
  environment: string;
  checks: Record<string, "ok" | "error" | "skipped">;
};

export type AuthBody = {
  email_or_username: string;
  password: string;
};

export type RegisterBody = {
  email: string;
  username: string;
  password: string;
};

export type CreateArtistBody = {
  display_name: string;
  full_name: string | null;
};

export type CreateTrackBody = {
  artist_id: string;
  title: string;
  album: string | null;
};

export type UploadUrlBody = {
  filename: string;
  content_type: string;
  size_bytes: number;
};

export type UploadCompleteBody = {
  object_key: string;
};

export type ArtistListResponse = {
  items: Artist[];
  limit: number;
  offset: number;
};

export type TrackListResponse = {
  items: Track[];
};
