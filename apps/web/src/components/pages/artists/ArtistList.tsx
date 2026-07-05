"use client";

import type { Artist } from "@lib/api";

type ArtistListProps = {
  artists: Artist[] | undefined;
  isLoading: boolean;
};

export function ArtistList({ artists, isLoading }: ArtistListProps) {
  return (
    <div className="space-y-3">
      {artists?.map((artist) => (
        <article className="row-card" key={artist.id}>
          <div>
            <h2 className="font-semibold">{artist.display_name}</h2>
            <p className="text-sm text-zinc-400">{artist.slug}</p>
          </div>
          {artist.full_name ? <p className="text-sm text-zinc-300">{artist.full_name}</p> : null}
        </article>
      ))}
      {isLoading ? <p className="text-sm text-zinc-400">Loading artists</p> : null}
    </div>
  );
}
