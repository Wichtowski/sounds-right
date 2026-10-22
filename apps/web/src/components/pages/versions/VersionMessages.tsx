"use client";

type VersionMessagesProps = {
  message: string;
  uploadError?: string;
  transcriptionError?: string;
};

export function VersionMessages({
  message,
  uploadError,
  transcriptionError,
}: VersionMessagesProps) {
  return (
    <>
      {message ? <p className="text-sm text-emerald-300" role="status">{message}</p> : null}
      {uploadError ? <p className="text-sm text-red-300" role="alert">{uploadError} Select your file and try uploading again.</p> : null}
      {transcriptionError ? <p className="text-sm text-red-300">{transcriptionError}</p> : null}
    </>
  );
}
