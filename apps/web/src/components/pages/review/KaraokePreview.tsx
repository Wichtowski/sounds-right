"use client";

import { useEffect, useMemo, useState } from "react";

import type { TranscriptDocument, TranscriptSegment } from "@lib/api";

import { formatTimestamp } from "./formatTimestamp";

type KaraokePreviewProps = {
  transcript: TranscriptDocument;
  currentTime: number;
  onTimeChange: (time: number) => void;
};

export function KaraokePreview({ transcript, currentTime, onTimeChange }: KaraokePreviewProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const duration = transcript.metadata.duration_seconds ?? transcript.segments.at(-1)?.end ?? 0;
  const activeSegment = useMemo(
    () => findActiveSegment(transcript.segments, currentTime),
    [currentTime, transcript.segments],
  );
  const activeWord = activeSegment?.words.find((word) => currentTime >= word.start && currentTime <= word.end);

  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    const startedAt = performance.now();
    const baseTime = currentTime;
    const frame = window.setInterval(() => {
      const nextTime = baseTime + (performance.now() - startedAt) / 1000;
      if (nextTime >= duration) {
        onTimeChange(duration);
        setIsPlaying(false);
        return;
      }
      onTimeChange(nextTime);
    }, 80);

    return () => window.clearInterval(frame);
  }, [currentTime, duration, isPlaying, onTimeChange]);

  return (
    <div className="row-card space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">Karaoke preview</h2>
          <p className="text-sm text-zinc-400">{formatTimestamp(currentTime)}</p>
        </div>
        <div className="flex gap-2">
          <button className="button-primary" disabled={duration <= 0} onClick={() => setIsPlaying(true)} type="button">
            Play
          </button>
          <button className="button-secondary" onClick={() => setIsPlaying(false)} type="button">
            Pause
          </button>
          <button
            className="button-secondary"
            onClick={() => {
              setIsPlaying(false);
              onTimeChange(0);
            }}
            type="button"
          >
            Reset
          </button>
        </div>
      </div>

      <input
        className="w-full accent-cyan-300"
        max={duration}
        min={0}
        onChange={(event) => onTimeChange(Number(event.target.value))}
        step={0.01}
        type="range"
        value={Math.min(currentTime, duration)}
      />

      <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
        <p className="text-lg leading-8 text-zinc-100">{activeSegment?.text || "No active segment"}</p>
        {activeSegment ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {activeSegment.words.map((word, index) => (
              <span
                className={`rounded px-2 py-1 text-sm ${
                  activeWord === word ? "bg-cyan-300 text-zinc-950" : "bg-zinc-900 text-zinc-300"
                }`}
                key={`${word.start}-${word.end}-${index}`}
              >
                {word.word}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function findActiveSegment(segments: TranscriptSegment[], currentTime: number) {
  return segments.find((segment) => currentTime >= segment.start && currentTime <= segment.end);
}
