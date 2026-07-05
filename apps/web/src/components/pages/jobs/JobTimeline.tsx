"use client";

type JobTimelineProps = {
  events: Array<{
    event_id: string;
    event_type: string;
    created_at: string;
    payload: Record<string, unknown>;
  }> | undefined;
  isLoading: boolean;
};

export function JobTimeline({ events, isLoading }: JobTimelineProps) {
  return (
    <div className="space-y-3">
      <h2 className="text-xl font-semibold">Timeline</h2>
      {events?.map((event) => (
        <article className="row-card space-y-2" key={event.event_id}>
          <div className="flex flex-wrap justify-between gap-3">
            <h3 className="font-semibold">{event.event_type}</h3>
            <time className="text-sm text-zinc-400">{new Date(event.created_at).toLocaleString()}</time>
          </div>
          <pre className="overflow-x-auto rounded bg-zinc-950 p-3 text-xs text-zinc-300">
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        </article>
      ))}
      {isLoading ? <p className="text-sm text-zinc-400">Loading events</p> : null}
    </div>
  );
}
