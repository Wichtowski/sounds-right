"use client";

import type { ReviewEvent } from "@lib/api";

type ReviewEventTimelineProps = {
  events: ReviewEvent[] | undefined;
  isLoading: boolean;
};

export function ReviewEventTimeline({ events, isLoading }: ReviewEventTimelineProps) {
  if (isLoading) {
    return <div className="row-card text-sm text-zinc-400">Loading review history...</div>;
  }

  if (!events?.length) {
    return <div className="row-card text-sm text-zinc-400">No review events have been recorded yet.</div>;
  }

  return (
    <div className="row-card space-y-4">
      <h2 className="text-xl font-semibold">Review history</h2>
      <ol className="space-y-3">
        {events.map((event) => (
          <li className="border-l border-zinc-700 pl-4" key={event.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-medium text-zinc-100">{event.action}</p>
              <time className="text-xs text-zinc-500">{new Date(event.created_at).toLocaleString()}</time>
            </div>
            <p className="text-sm text-zinc-400">By {event.reviewer.username}</p>
            {event.reason ? <p className="mt-2 text-sm text-zinc-300">{event.reason}</p> : null}
          </li>
        ))}
      </ol>
    </div>
  );
}
