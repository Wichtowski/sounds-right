"use client";

type VersionMessagesProps = {
  message: string;
  uploadUrlError?: string;
  completeError?: string;
  transcriptionError?: string;
};

export function VersionMessages({
  message,
  uploadUrlError,
  completeError,
  transcriptionError,
}: VersionMessagesProps) {
  return (
    <>
      {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      {uploadUrlError ? <p className="text-sm text-red-300">{uploadUrlError}</p> : null}
      {completeError ? <p className="text-sm text-red-300">{completeError}</p> : null}
      {transcriptionError ? <p className="text-sm text-red-300">{transcriptionError}</p> : null}
    </>
  );
}
