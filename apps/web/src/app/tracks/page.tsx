"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@components/AppShell";
import { TrackForm } from "@components/pages/tracks/TrackForm";
import { TrackList } from "@components/pages/tracks/TrackList";
import { api } from "@lib/api";

export default function TracksPage() {
  const queryClient = useQueryClient();
  const [artistId, setArtistId] = useState("");
  const [title, setTitle] = useState("");
  const [album, setAlbum] = useState("");

  const artistsQuery = useQuery({
    queryKey: ["artists"],
    queryFn: () => api.artists.list(),
  });
  const tracksQuery = useQuery({
    queryKey: ["tracks"],
    queryFn: () => api.tracks.list(),
  });

  const createMutation = useMutation({
    mutationFn: () => api.tracks.create({ artist_id: artistId, title, album: album || null }),
    onSuccess: async () => {
      setTitle("");
      setAlbum("");
      await queryClient.invalidateQueries({ queryKey: ["tracks"] });
    },
  });

  return (
    <AppShell>
      <section className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr]">
        <TrackForm
          album={album}
          artistId={artistId}
          artistOptions={artistsQuery.data?.items ?? []}
          errorMessage={createMutation.error?.message}
          isSubmitting={createMutation.isPending}
          onAlbumChange={setAlbum}
          onArtistChange={setArtistId}
          onSubmit={() => createMutation.mutate()}
          onTitleChange={setTitle}
          title={title}
        />
        <TrackList tracks={tracksQuery.data?.items} isLoading={tracksQuery.isLoading} />
      </section>
    </AppShell>
  );
}
