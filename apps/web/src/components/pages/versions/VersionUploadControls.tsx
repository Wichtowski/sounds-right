"use client";

type VersionUploadControlsProps = {
  canRequestUploadUrl: boolean;
  canCompleteUpload: boolean;
  canStartTranscription: boolean;
  onRequestUploadUrl: () => void;
  onCompleteUpload: () => void;
  onStartTranscription: () => void;
  selectedFileName?: string | null;
  objectKey?: string | null;
  isRequestingUploadUrl: boolean;
  isCompletingUpload: boolean;
  isStartingTranscription: boolean;
};

export function VersionUploadControls({
  canRequestUploadUrl,
  canCompleteUpload,
  canStartTranscription,
  onRequestUploadUrl,
  onCompleteUpload,
  onStartTranscription,
  selectedFileName,
  objectKey,
  isRequestingUploadUrl,
  isCompletingUpload,
  isStartingTranscription,
}: VersionUploadControlsProps) {
  return (
    <div className="space-y-4">
      {selectedFileName ? <p className="text-sm text-zinc-400">Selected file: {selectedFileName}</p> : null}
      <div className="flex flex-wrap gap-3">
        <button className="button-secondary" disabled={!canRequestUploadUrl || isRequestingUploadUrl} onClick={onRequestUploadUrl}>
          Request upload URL
        </button>
        <button className="button-primary" disabled={!canCompleteUpload || isCompletingUpload} onClick={onCompleteUpload}>
          Upload and complete
        </button>
        <button className="button-primary" disabled={!canStartTranscription || isStartingTranscription} onClick={onStartTranscription}>
          Start transcription
        </button>
      </div>
      {objectKey ? <p className="break-all text-sm text-zinc-400">Object key: {objectKey}</p> : null}
    </div>
  );
}
