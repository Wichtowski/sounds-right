"use client";

import type { TrackVersion } from "@lib/api";

type VersionListProps = {
  versions: TrackVersion[] | undefined;
  isLoading: boolean;
};

export function VersionList({ versions, isLoading }: VersionListProps) {
  return (
    <div className="space-y-3">
      {versions?.map((version) => (
        <a className="row-card block" href={`/versions/${version.id}`} key={version.id}>
          <h2 className="font-semibold">Version {version.version}</h2>
          <p className="text-sm text-zinc-400">{version.status}</p>
        </a>
      ))}
      {isLoading ? <p className="text-sm text-zinc-400">Loading versions</p> : null}
    </div>
  );
}
