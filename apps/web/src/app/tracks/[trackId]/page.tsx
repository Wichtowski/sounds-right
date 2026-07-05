"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AppShell } from "@components/AppShell";
import { TrackHeader } from "@components/pages/tracks/TrackHeader";
import { VersionList } from "@components/pages/tracks/VersionList";
import { api } from "@lib/api";

type TrackDetailPageProps = {
  params: {
    trackId: string;
  };
};

export default function TrackDetailPage({ params }: TrackDetailPageProps) {
  const queryClient = useQueryClient();
  const trackQuery = useQuery({
    queryKey: ["track", params.trackId],
    queryFn: () => api.tracks.get(params.trackId),
  });
  const versionsQuery = useQuery({
    queryKey: ["track-versions", params.trackId],
    queryFn: () => api.tracks.versions(params.trackId),
  });

  const createVersionMutation = useMutation({
    mutationFn: () => api.tracks.createVersion(params.trackId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["track-versions", params.trackId] });
    },
  });

  return (
    <AppShell>
      <section className="space-y-6">
        <TrackHeader
          artistName={trackQuery.data?.artist?.display_name}
          errorMessage={createVersionMutation.error?.message}
          isSubmitting={createVersionMutation.isPending}
          onCreateVersion={() => createVersionMutation.mutate()}
          title={trackQuery.data?.title ?? "Track"}
        />
        <VersionList isLoading={versionsQuery.isLoading} versions={versionsQuery.data} />
      </section>
    </AppShell>
  );
}
