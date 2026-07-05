"use client";

type JobOverviewCardProps = {
  status?: string;
  engine?: string;
  progress?: number;
  errorMessage?: string | null;
};

export function JobOverviewCard({ status, engine, progress, errorMessage }: JobOverviewCardProps) {
  return (
    <div className="row-card space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-zinc-400">Status</p>
          <p className="text-xl font-semibold">{status ?? "loading"}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-zinc-400">Engine</p>
          <p className="font-medium">{engine ?? "unknown"}</p>
        </div>
      </div>
      <div className="h-3 overflow-hidden rounded bg-zinc-800">
        <div className="h-full bg-emerald-400" style={{ width: `${progress ?? 0}%` }} />
      </div>
      <p className="text-sm text-zinc-400">{progress ?? 0}% complete</p>
      {errorMessage ? <p className="text-sm text-red-300">{errorMessage}</p> : null}
    </div>
  );
}
