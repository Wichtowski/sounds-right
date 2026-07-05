"use client";

import { useState } from "react";

import type { TrackVersion } from "@lib/api";

type ReviewActionsProps = {
  approveError: string | undefined;
  isApproving: boolean;
  isPublishing: boolean;
  isRejecting: boolean;
  onApprove: () => void;
  onPublish: () => void;
  onReject: (reason: string) => void;
  publishError: string | undefined;
  publishedUrl: string | undefined;
  rejectError: string | undefined;
  version: TrackVersion | undefined;
};

export function ReviewActions({
  approveError,
  isApproving,
  isPublishing,
  isRejecting,
  onApprove,
  onPublish,
  onReject,
  publishError,
  publishedUrl,
  rejectError,
  version,
}: ReviewActionsProps) {
  const [isRejectOpen, setIsRejectOpen] = useState(false);
  const [reason, setReason] = useState("");

  if (!version) {
    return <div className="row-card text-sm text-zinc-400">Loading review actions...</div>;
  }

  if (version.status === "approved") {
    return (
      <div className="row-card space-y-4">
        <div>
          <h2 className="text-xl font-semibold">Publication</h2>
          <p className="text-sm text-emerald-200">This version has been approved.</p>
        </div>
        <button className="button-primary" disabled={isPublishing} onClick={onPublish} type="button">
          {isPublishing ? "Publishing..." : "Publish"}
        </button>
        {publishedUrl ? (
          <a className="block text-sm text-cyan-200 hover:text-cyan-100" href={publishedUrl}>
            Open public preview
          </a>
        ) : null}
        {publishError ? <p className="text-sm text-red-200">{publishError}</p> : null}
      </div>
    );
  }

  if (version.status === "published") {
    return (
      <div className="row-card space-y-2 text-sm">
        <p className="font-medium text-emerald-200">This version is published.</p>
        {publishedUrl ? (
          <a className="text-cyan-200 hover:text-cyan-100" href={publishedUrl}>
            Open public preview
          </a>
        ) : null}
      </div>
    );
  }

  if (version.status === "rejected") {
    return (
      <div className="row-card space-y-2 text-sm">
        <p className="font-medium text-amber-200">This version has been rejected.</p>
        {version.rejection_reason ? <p className="text-zinc-300">{version.rejection_reason}</p> : null}
      </div>
    );
  }

  if (version.status !== "completed") {
    return <div className="row-card text-sm text-zinc-400">This version is not ready for review.</div>;
  }

  return (
    <div className="row-card space-y-4">
      <div>
        <h2 className="text-xl font-semibold">Review actions</h2>
        <p className="text-sm text-zinc-400">Approve or reject this completed transcription.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <button className="button-primary" disabled={isApproving} onClick={onApprove} type="button">
          {isApproving ? "Approving..." : "Approve"}
        </button>
        <button className="button-secondary" disabled={isRejecting} onClick={() => setIsRejectOpen(true)} type="button">
          Reject
        </button>
      </div>
      {approveError ? <p className="text-sm text-red-200">{approveError}</p> : null}
      {isRejectOpen ? (
        <div className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-950 p-4">
          <label className="block space-y-2">
            <span className="text-sm font-medium text-zinc-200">Rejection reason</span>
            <textarea
              className="field min-h-28"
              maxLength={2000}
              onChange={(event) => setReason(event.target.value)}
              value={reason}
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              className="button-primary"
              disabled={isRejecting || reason.trim().length === 0}
              onClick={() => onReject(reason.trim())}
              type="button"
            >
              {isRejecting ? "Rejecting..." : "Submit rejection"}
            </button>
            <button className="button-secondary" onClick={() => setIsRejectOpen(false)} type="button">
              Cancel
            </button>
          </div>
          {rejectError ? <p className="text-sm text-red-200">{rejectError}</p> : null}
        </div>
      ) : null}
    </div>
  );
}
