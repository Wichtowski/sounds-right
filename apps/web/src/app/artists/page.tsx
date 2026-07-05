"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@components/AppShell";
import { ArtistForm } from "@components/pages/artists/ArtistForm";
import { ArtistList } from "@components/pages/artists/ArtistList";
import { api } from "@lib/api";

export default function ArtistsPage() {
  const queryClient = useQueryClient();
  const [displayName, setDisplayName] = useState("");
  const [fullName, setFullName] = useState("");

  const artistsQuery = useQuery({
    queryKey: ["artists"],
    queryFn: () => api.artists.list(),
  });

  const createMutation = useMutation({
    mutationFn: () => api.artists.create({ display_name: displayName, full_name: fullName || null }),
    onSuccess: async () => {
      setDisplayName("");
      setFullName("");
      await queryClient.invalidateQueries({ queryKey: ["artists"] });
    },
  });

  return (
    <AppShell>
      <section className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr]">
        <ArtistForm
          displayName={displayName}
          errorMessage={createMutation.error?.message}
          fullName={fullName}
          isSubmitting={createMutation.isPending}
          onDisplayNameChange={setDisplayName}
          onFullNameChange={setFullName}
          onSubmit={() => createMutation.mutate()}
        />
        <ArtistList artists={artistsQuery.data?.items} isLoading={artistsQuery.isLoading} />
      </section>
    </AppShell>
  );
}
