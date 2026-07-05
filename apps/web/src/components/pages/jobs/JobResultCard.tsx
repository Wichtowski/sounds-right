"use client";

import type { TrackVersion } from "@lib/api";

type JobResultCardProps = {
  version: TrackVersion;
};

export function JobResultCard({ version }: JobResultCardProps) {
  return (
    <div className="row-card space-y-2">
      <h2 className="text-xl font-semibold">Result</h2>
      <p className="text-sm text-zinc-400">Transcription completed</p>
      <dl className="space-y-1 text-sm">
        <div className="flex justify-between gap-3">
          <dt className="text-zinc-400">Transcript</dt>
          <dd className="break-all font-mono text-xs text-zinc-200">{version.transcript_object_key}</dd>
        </div>
        {version.manifest_object_key ? (
          <div className="flex justify-between gap-3">
            <dt className="text-zinc-400">Manifest</dt>
            <dd className="break-all font-mono text-xs text-zinc-200">{version.manifest_object_key}</dd>
          </div>
        ) : null}
        {version.word_count != null ? (
          <div className="flex justify-between gap-3">
            <dt className="text-zinc-400">Words</dt>
            <dd className="text-zinc-200">{version.word_count}</dd>
          </div>
        ) : null}
        {version.duration_seconds != null ? (
          <div className="flex justify-between gap-3">
            <dt className="text-zinc-400">Duration</dt>
            <dd className="text-zinc-200">{version.duration_seconds.toFixed(2)}s</dd>
          </div>
        ) : null}
      </dl>
      <a className="button-primary inline-flex" href={`/versions/${version.id}/review`}>
        Open review
      </a>
    </div>
  );
}
