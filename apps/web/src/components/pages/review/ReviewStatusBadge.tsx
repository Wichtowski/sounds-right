"use client";

import type { TrackVersion } from "@lib/api";

type ReviewStatusBadgeProps = {
  status: TrackVersion["status"] | "loading";
};

const statusClasses: Record<string, string> = {
  approved: "border-emerald-500/50 bg-emerald-500/10 text-emerald-200",
  completed: "border-cyan-500/50 bg-cyan-500/10 text-cyan-200",
  failed: "border-red-500/50 bg-red-500/10 text-red-200",
  rejected: "border-amber-500/50 bg-amber-500/10 text-amber-200",
};

export function ReviewStatusBadge({ status }: ReviewStatusBadgeProps) {
  return (
    <span
      className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold uppercase tracking-wide ${
        statusClasses[status] ?? "border-zinc-700 bg-zinc-900 text-zinc-300"
      }`}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}
