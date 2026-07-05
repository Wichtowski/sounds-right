"use client";

import { useQuery } from "@tanstack/react-query";

import { AppShell } from "@components/AppShell";
import { JobOverviewCard } from "@components/pages/jobs/JobOverviewCard";
import { JobResultCard } from "@components/pages/jobs/JobResultCard";
import { JobTimeline } from "@components/pages/jobs/JobTimeline";
import { api } from "@lib/api";

type JobDetailPageProps = {
  params: {
    jobId: string;
  };
};

const activeStatuses = new Set(["queued", "started", "processing"]);

export default function JobDetailPage({ params }: JobDetailPageProps) {
  const jobQuery = useQuery({
    queryKey: ["job", params.jobId],
    queryFn: () => api.jobs.get(params.jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && activeStatuses.has(status) ? 1500 : false;
    },
  });
  const eventsQuery = useQuery({
    queryKey: ["job-events", params.jobId],
    queryFn: () => api.jobs.events(params.jobId),
    refetchInterval: (query) => {
      const status = jobQuery.data?.status ?? query.state.data?.events.at(-1)?.event_type;
      return status && !String(status).includes("completed") && !String(status).includes("failed")
        ? 1500
        : false;
    },
  });

  const job = jobQuery.data;

  const versionQuery = useQuery({
    queryKey: ["job-version", job?.track_version_id],
    queryFn: () => api.versions.get(job?.track_version_id ?? ""),
    enabled: Boolean(job?.track_version_id) && job?.status === "completed",
  });
  const version = versionQuery.data;

  return (
    <AppShell>
      <section className="max-w-3xl space-y-6">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold">Transcription job</h1>
          <p className="text-sm text-zinc-400">{params.jobId}</p>
        </div>

        <JobOverviewCard
          engine={job?.engine}
          errorMessage={job?.error_message}
          progress={job?.progress}
          status={job?.status}
        />

        {job?.status === "completed" && version?.transcript_object_key ? <JobResultCard version={version} /> : null}

        <JobTimeline events={eventsQuery.data?.events} isLoading={eventsQuery.isLoading} />
      </section>
    </AppShell>
  );
}
