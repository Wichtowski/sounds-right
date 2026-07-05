"use client";

import type { TranscriptDocument, TranscriptSegment } from "@lib/api";

import { formatTimestamp } from "./formatTimestamp";

type TranscriptSegmentListProps = {
  activeSegmentId: TranscriptSegment["id"] | null;
  onSeek: (time: number) => void;
  transcript: TranscriptDocument;
};

export function TranscriptSegmentList({ activeSegmentId, onSeek, transcript }: TranscriptSegmentListProps) {
  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold">Segments</h2>
      {transcript.segments.length === 0 ? (
        <div className="row-card text-sm text-zinc-400">No segments were found in this transcript.</div>
      ) : (
        transcript.segments.map((segment) => (
          <button
            className={`row-card block w-full text-left transition ${
              activeSegmentId === segment.id ? "border-cyan-400 bg-cyan-950/30" : "hover:border-zinc-600"
            }`}
            key={segment.id}
            onClick={() => onSeek(segment.start)}
            type="button"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <p className="font-medium text-zinc-100">{segment.text}</p>
              <span className="font-mono text-xs text-zinc-400">
                {formatTimestamp(segment.start)} - {formatTimestamp(segment.end)}
              </span>
            </div>
            {segment.words.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {segment.words.map((word, index) => (
                  <span className="rounded bg-zinc-900 px-2 py-1 text-xs text-zinc-300" key={`${word.start}-${index}`}>
                    {word.word} {formatTimestamp(word.start)}-{formatTimestamp(word.end)}
                  </span>
                ))}
              </div>
            ) : null}
          </button>
        ))
      )}
    </div>
  );
}
