"use client";

import type { ReviewQueueItem } from "@lib/api";

import { formatTimestamp } from "./formatTimestamp";
import { ReviewStatusBadge } from "./ReviewStatusBadge";

type ReviewQueueTableProps = {
  isLoading: boolean;
  items: ReviewQueueItem[] | undefined;
};

export function ReviewQueueTable({ isLoading, items }: ReviewQueueTableProps) {
  if (isLoading) {
    return <div className="row-card text-sm text-zinc-400">Loading review queue...</div>;
  }

  if (!items?.length) {
    return <div className="row-card text-sm text-zinc-400">No transcriptions found for this filter.</div>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-800">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="bg-zinc-900 text-xs uppercase tracking-wide text-zinc-400">
          <tr>
            <th className="px-4 py-3">Track</th>
            <th className="px-4 py-3">Version</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Summary</th>
            <th className="px-4 py-3">Updated</th>
            <th className="px-4 py-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800 bg-zinc-950">
          {items.map((item) => (
            <tr className="align-top" key={item.version_id}>
              <td className="px-4 py-4">
                <div className="font-medium text-zinc-100">{item.track.title}</div>
                <div className="text-xs text-zinc-400">{item.artist.display_name}</div>
                {item.track.album ? <div className="text-xs text-zinc-500">{item.track.album}</div> : null}
              </td>
              <td className="px-4 py-4 text-zinc-300">v{item.version}</td>
              <td className="px-4 py-4">
                <ReviewStatusBadge status={item.status} />
              </td>
              <td className="px-4 py-4 text-zinc-300">
                <div>{item.summary.engine ?? "Unknown engine"}</div>
                <div className="text-xs text-zinc-500">
                  {item.summary.word_count ?? 0} words
                  {item.summary.duration_seconds != null
                    ? ` - ${formatTimestamp(item.summary.duration_seconds)}`
                    : ""}
                </div>
              </td>
              <td className="px-4 py-4 text-xs text-zinc-400">{new Date(item.updated_at).toLocaleString()}</td>
              <td className="px-4 py-4 text-right">
                <a className="button-secondary inline-flex" href={`/versions/${item.version_id}/review`}>
                  Open review
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
