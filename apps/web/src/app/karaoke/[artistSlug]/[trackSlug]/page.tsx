"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { AppShell } from "@components/AppShell";
import { KaraokePreview } from "@components/pages/review/KaraokePreview";
import { TranscriptSegmentList } from "@components/pages/review/TranscriptSegmentList";
import { api, type TranscriptSegment } from "@lib/api";

type PublicKaraokePageProps = {
  params: {
    artistSlug: string;
    trackSlug: string;
  };
};

export default function PublicKaraokePage({ params }: PublicKaraokePageProps) {
  const [currentTime, setCurrentTime] = useState(0);
  const karaokeQuery = useQuery({
    queryKey: ["public-karaoke-latest", params.artistSlug, params.trackSlug],
    queryFn: () => api.publicKaraoke.latest(params.artistSlug, params.trackSlug),
    retry: false,
  });
  const document = karaokeQuery.data;
  const transcript = document?.transcript;
  const activeSegment = useMemo<TranscriptSegment | undefined>(
    () => transcript?.segments.find((segment) => currentTime >= segment.start && currentTime <= segment.end),
    [currentTime, transcript?.segments],
  );

  return (
    <AppShell>
      <section className="space-y-6">
        <div className="space-y-2">
          <p className="text-sm font-medium text-cyan-200">Public karaoke</p>
          <h1 className="text-3xl font-semibold">
            {document ? `${document.manifest.artist.display_name} - ${document.manifest.track.title}` : "Loading"}
          </h1>
          {document?.manifest.latest_version ? (
            <p className="text-sm text-zinc-400">Published version {document.manifest.latest_version}</p>
          ) : null}
        </div>

        {karaokeQuery.error ? (
          <div className="row-card text-sm text-red-200">Published karaoke transcript is unavailable.</div>
        ) : null}

        {transcript ? (
          <div className="space-y-6">
            <KaraokePreview currentTime={currentTime} onTimeChange={setCurrentTime} transcript={transcript} />
            <TranscriptSegmentList
              activeSegmentId={activeSegment?.id ?? null}
              onSeek={setCurrentTime}
              transcript={transcript}
            />
          </div>
        ) : null}
      </section>
    </AppShell>
  );
}
