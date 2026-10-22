"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChangeEvent, use, useState } from "react";

import { AppShell } from "@components/AppShell";
import { VersionHeader } from "@components/pages/versions/VersionHeader";
import { VersionMessages } from "@components/pages/versions/VersionMessages";
import { VersionUploadControls } from "@components/pages/versions/VersionUploadControls";
import { api } from "@lib/api";

type VersionDetailPageProps = {
  params: Promise<{
    versionId: string;
  }>;
};

export default function VersionDetailPage({ params: routeParams }: VersionDetailPageProps) {
  const params = use(routeParams);
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  const versionQuery = useQuery({
    queryKey: ["version", params.versionId],
    queryFn: () => api.versions.get(params.versionId),
  });

  const uploadMutation = useMutation({
    onMutate: () => setMessage(""),
    mutationFn: async () => {
      if (!file) {
        throw new Error("Choose an audio file first");
      }
      const uploadUrl = await api.versions.uploadUrl(params.versionId, {
        filename: file.name,
        content_type: file.type || "audio/mpeg",
        size_bytes: file.size,
      });
      const uploadResponse = await fetch(uploadUrl.upload_url, {
        method: uploadUrl.method,
        headers: uploadUrl.headers,
        body: file,
      });
      if (!uploadResponse.ok) {
        throw new Error("Audio upload failed.");
      }

      return api.versions.uploadComplete(params.versionId, { object_key: uploadUrl.object_key });
    },
    onSuccess: () => setMessage("Upload completed. You can now start transcription."),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["version", params.versionId] }),
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
    setMessage("");
    uploadMutation.reset();
  }

  const canUpload = ["draft", "upload_url_created"].includes(versionQuery.data?.status ?? "");
  const isBusy = uploadMutation.isPending || startTranscriptionMutation.isPending;

  return (
    <AppShell>
      <section className="max-w-2xl space-y-6">
        <VersionHeader status={versionQuery.data?.status ?? "loading"} version={versionQuery.data?.version ?? ""} />
        <div className="space-y-4">
          <label className="block space-y-2">
            <span className="text-sm font-medium">Audio file</span>
            <input
              accept=".mp3,.wav,.flac,.m4a,.ogg,audio/*"
              className="field"
              disabled={!canUpload || isBusy}
              onChange={chooseFile}
              type="file"
            />
          </label>
          <VersionUploadControls
            canUpload={canUpload && Boolean(file)}
            canStartTranscription={versionQuery.data?.status === "uploaded"}
            isUploading={uploadMutation.isPending}
            isStartingTranscription={startTranscriptionMutation.isPending}
            onUpload={() => uploadMutation.mutate()}
            onStartTranscription={() => startTranscriptionMutation.mutate()}
            selectedFileName={file?.name}
          />
        </div>
        <VersionMessages
          uploadError={uploadMutation.error?.message}
          message={message}
          transcriptionError={startTranscriptionMutation.error?.message}
        />
      </section>
    </AppShell>
  );
}
