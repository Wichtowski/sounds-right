"use client";

import type { Track } from "@lib/api";

type TrackListProps = {
  tracks: Track[] | undefined;
  isLoading: boolean;
};

export function TrackList({ tracks, isLoading }: TrackListProps) {
  return (
    <div className="space-y-3">
      {tracks?.map((track) => (
        <a className="row-card block" href={`/tracks/${track.id}`} key={track.id}>
          <h2 className="font-semibold">{track.title}</h2>
          <p className="text-sm text-zinc-400">
            {track.artist?.display_name ?? "Unknown artist"} / {track.slug}
          </p>
          {track.album ? <p className="text-sm text-zinc-300">{track.album}</p> : null}
        </a>
      ))}
      {isLoading ? <p className="text-sm text-zinc-400">Loading tracks</p> : null}
    </div>
  );
}
