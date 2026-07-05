"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChangeEvent, useState } from "react";

import { AppShell } from "@components/AppShell";
import { VersionHeader } from "@components/pages/versions/VersionHeader";
import { VersionMessages } from "@components/pages/versions/VersionMessages";
import { VersionUploadControls } from "@components/pages/versions/VersionUploadControls";
import { api, type UploadUrl } from "@lib/api";

type VersionDetailPageProps = {
  params: {
    versionId: string;
  };
};

export default function VersionDetailPage({ params }: VersionDetailPageProps) {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [uploadUrl, setUploadUrl] = useState<UploadUrl | null>(null);
  const [message, setMessage] = useState("");

  const versionQuery = useQuery({
    queryKey: ["version", params.versionId],
    queryFn: () => api.versions.get(params.versionId),
  });

  const uploadUrlMutation = useMutation({
    mutationFn: async () => {
      if (!file) {
        throw new Error("Choose an audio file first");
      }
      return api.versions.uploadUrl(params.versionId, {
        filename: file.name,
        content_type: file.type || "audio/mpeg",
        size_bytes: file.size,
      });
    },
    onSuccess: async (data) => {
      setUploadUrl(data);
      setMessage("Upload URL created");
      await queryClient.invalidateQueries({ queryKey: ["version", params.versionId] });
    },
  });

  const completeMutation = useMutation({
    mutationFn: async () => {
      if (!file || !uploadUrl) {
        throw new Error("Create an upload URL first");
      }

      const uploadResponse = await fetch(uploadUrl.upload_url, {
        method: uploadUrl.method,
        headers: uploadUrl.headers,
        body: file,
      });
      if (!uploadResponse.ok) {
        throw new Error(`MinIO upload failed with ${uploadResponse.status}`);
      }

      return api.versions.uploadComplete(params.versionId, { object_key: uploadUrl.object_key });
    },
    onSuccess: async () => {
      setMessage("Upload completed");
      await queryClient.invalidateQueries({ queryKey: ["version", params.versionId] });
    },
  });

  const startTranscriptionMutation = useMutation({
    mutationFn: () => api.versions.startTranscription(params.versionId),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ["version", params.versionId] });
      window.location.href = `/jobs/${data.job_id}`;
    },
  });

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setUploadUrl(null);
    setMessage("");
  }

  return (
    <AppShell>
      <section className="max-w-2xl space-y-6">
        <VersionHeader status={versionQuery.data?.status ?? "loading"} version={versionQuery.data?.version ?? ""} />
        <div className="space-y-4">
          <input accept=".mp3,.wav,.flac,.m4a,.ogg,audio/*" className="field" onChange={chooseFile} type="file" />
          <VersionUploadControls
            canCompleteUpload={Boolean(file && uploadUrl)}
            canRequestUploadUrl={Boolean(file)}
            canStartTranscription={versionQuery.data?.status === "uploaded"}
            isCompletingUpload={completeMutation.isPending}
            isRequestingUploadUrl={uploadUrlMutation.isPending}
            isStartingTranscription={startTranscriptionMutation.isPending}
            objectKey={uploadUrl?.object_key}
            onCompleteUpload={() => completeMutation.mutate()}
            onRequestUploadUrl={() => uploadUrlMutation.mutate()}
            onStartTranscription={() => startTranscriptionMutation.mutate()}
            selectedFileName={file?.name}
          />
        </div>
        <VersionMessages
          completeError={completeMutation.error?.message}
          message={message}
          transcriptionError={startTranscriptionMutation.error?.message}
          uploadUrlError={uploadUrlMutation.error?.message}
        />
      </section>
    </AppShell>
  );
}
