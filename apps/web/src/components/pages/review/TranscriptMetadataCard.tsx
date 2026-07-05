"use client";

import type { TrackVersion, TranscriptDocument } from "@lib/api";

import { formatTimestamp } from "./formatTimestamp";

type TranscriptMetadataCardProps = {
  transcript: TranscriptDocument | undefined;
  version: TrackVersion | undefined;
};

export function TranscriptMetadataCard({ transcript, version }: TranscriptMetadataCardProps) {
  return (
    <div className="row-card space-y-3">
      <h2 className="text-xl font-semibold">Transcript metadata</h2>
      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <MetadataRow label="Schema" value={transcript?.schema_version ?? version?.transcript_schema_version ?? "Unknown"} />
        <MetadataRow label="Engine" value={transcript?.engine.name ?? "Unknown"} />
        <MetadataRow label="Model" value={transcript?.engine.model ?? "Unknown"} />
        <MetadataRow label="Language" value={transcript?.engine.language ?? "Unknown"} />
        <MetadataRow
          label="Duration"
          value={
            transcript?.metadata.duration_seconds != null
              ? formatTimestamp(transcript.metadata.duration_seconds)
              : version?.duration_seconds != null
                ? formatTimestamp(version.duration_seconds)
                : "Unknown"
          }
        />
        <MetadataRow
          label="Words"
          value={String(transcript?.metadata.word_count ?? version?.word_count ?? "Unknown")}
        />
      </dl>
    </div>
  );
}

function MetadataRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-zinc-500">{label}</dt>
      <dd className="mt-1 text-zinc-100">{value}</dd>
    </div>
  );
}
