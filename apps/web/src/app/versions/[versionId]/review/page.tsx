"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { AppShell } from "@components/AppShell";
import { KaraokePreview } from "@components/pages/review/KaraokePreview";
import { ReviewActions } from "@components/pages/review/ReviewActions";
import { ReviewEventTimeline } from "@components/pages/review/ReviewEventTimeline";
import { ReviewStatusBadge } from "@components/pages/review/ReviewStatusBadge";
import { TranscriptMetadataCard } from "@components/pages/review/TranscriptMetadataCard";
import { TranscriptSegmentList } from "@components/pages/review/TranscriptSegmentList";
import { api, type TranscriptSegment } from "@lib/api";

type VersionReviewPageProps = {
  params: {
    versionId: string;
  };
};

export default function VersionReviewPage({ params }: VersionReviewPageProps) {
  const queryClient = useQueryClient();
  const [currentTime, setCurrentTime] = useState(0);
  const [publishedUrl, setPublishedUrl] = useState<string | undefined>();

  const versionQuery = useQuery({
    queryKey: ["version", params.versionId],
    queryFn: () => api.versions.get(params.versionId),
  });
  const transcriptQuery = useQuery({
    queryKey: ["version-transcript", params.versionId],
    queryFn: () => api.versions.transcript(params.versionId),
    retry: false,
  });
  const reviewEventsQuery = useQuery({
    queryKey: ["version-review-events", params.versionId],
    queryFn: () => api.versions.reviewEvents(params.versionId),
  });

  const approveMutation = useMutation({
    mutationFn: () => api.versions.approve(params.versionId),
    onSuccess: refreshReviewQueries,
  });
  const rejectMutation = useMutation({
    mutationFn: (reason: string) => api.versions.reject(params.versionId, reason),
    onSuccess: refreshReviewQueries,
  });
  const publishMutation = useMutation({
    mutationFn: () => api.versions.publish(params.versionId),
    onSuccess: async (publication) => {
      setPublishedUrl(publicPreviewUrl(publication.public_urls.latest ?? publication.public_urls.version));
      await refreshReviewQueries();
    },
  });

  const activeSegment = useMemo<TranscriptSegment | undefined>(
    () =>
      transcriptQuery.data?.segments.find((segment) => currentTime >= segment.start && currentTime <= segment.end),
    [currentTime, transcriptQuery.data?.segments],
  );
  const version = versionQuery.data;
  const transcript = transcriptQuery.data;

  async function refreshReviewQueries() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["review-queue"] }),
      queryClient.invalidateQueries({ queryKey: ["version", params.versionId] }),
      queryClient.invalidateQueries({ queryKey: ["version-review-events", params.versionId] }),
    ]);
  }

  return (
    <AppShell>
      <section className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <a className="text-sm text-cyan-200 hover:text-cyan-100" href="/review">
              Back to review queue
            </a>
            <h1 className="text-3xl font-semibold">
              {transcript?.track
                ? `${transcript.track.artist} - ${transcript.track.title}`
                : `Version ${version?.version ?? ""} review`}
            </h1>
            <p className="text-sm text-zinc-400">{params.versionId}</p>
          </div>
          <ReviewStatusBadge status={version?.status ?? "loading"} />
        </div>

        {versionQuery.error ? <div className="row-card text-sm text-red-200">{versionQuery.error.message}</div> : null}
        {transcriptQuery.error ? (
          <div className="row-card text-sm text-red-200">Transcript artifact is missing or unavailable.</div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-6">
            <TranscriptMetadataCard transcript={transcript} version={version} />
            {transcript ? (
              <KaraokePreview currentTime={currentTime} onTimeChange={setCurrentTime} transcript={transcript} />
            ) : null}
            {transcript ? (
              <TranscriptSegmentList
                activeSegmentId={activeSegment?.id ?? null}
                onSeek={setCurrentTime}
                transcript={transcript}
              />
            ) : null}
          </div>

          <aside className="space-y-6">
            <ReviewActions
              approveError={approveMutation.error?.message}
              isApproving={approveMutation.isPending}
              isPublishing={publishMutation.isPending}
              isRejecting={rejectMutation.isPending}
              onApprove={() => approveMutation.mutate()}
              onPublish={() => publishMutation.mutate()}
              onReject={(reason) => rejectMutation.mutate(reason)}
              publishError={publishMutation.error?.message}
              publishedUrl={publishedUrl}
              rejectError={rejectMutation.error?.message}
              version={version}
            />
            <ReviewEventTimeline events={reviewEventsQuery.data?.items} isLoading={reviewEventsQuery.isLoading} />
          </aside>
        </div>
      </section>
    </AppShell>
  );
}

function publicPreviewUrl(apiUrl: string) {
  const match = apiUrl.match(/^\/api\/public\/karaoke\/([^/]+)\/([^/]+)/);

  if (!match) {
    return apiUrl;
  }

  return `/karaoke/${match[1]}/${match[2]}`;
}
