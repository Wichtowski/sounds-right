"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@components/AppShell";
import { ReviewQueueTable } from "@components/pages/review/ReviewQueueTable";
import { api, type ReviewQueueStatus } from "@lib/api";

const filters: Array<{ label: string; status: ReviewQueueStatus }> = [
  { label: "Completed", status: "completed" },
  { label: "Approved", status: "approved" },
  { label: "Rejected", status: "rejected" },
  { label: "Failed", status: "failed" },
];

export default function ReviewPage() {
  const [status, setStatus] = useState<ReviewQueueStatus>("completed");
  const queueQuery = useQuery({
    queryKey: ["review-queue", status, 20, 0],
    queryFn: () => api.review.queue(status),
  });

  return (
    <AppShell>
      <section className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold">Review queue</h1>
          <p className="max-w-2xl text-sm text-zinc-400">
            Inspect completed transcript artifacts, review timing, and record approval decisions.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {filters.map((filter) => (
            <button
              className={filter.status === status ? "button-primary" : "button-secondary"}
              key={filter.status}
              onClick={() => setStatus(filter.status)}
              type="button"
            >
              {filter.label}
            </button>
          ))}
        </div>

        {queueQuery.error ? <div className="row-card text-sm text-red-200">{queueQuery.error.message}</div> : null}
        <ReviewQueueTable isLoading={queueQuery.isLoading} items={queueQuery.data?.items} />
      </section>
    </AppShell>
  );
}
