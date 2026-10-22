"use client";

type VersionUploadControlsProps = {
  canUpload: boolean;
  canStartTranscription: boolean;
  onUpload: () => void;
  onStartTranscription: () => void;
  selectedFileName?: string | null;
  isUploading: boolean;
  isStartingTranscription: boolean;
};

export function VersionUploadControls({
  canUpload,
  canStartTranscription,
  onUpload,
  onStartTranscription,
  selectedFileName,
  isUploading,
  isStartingTranscription,
}: VersionUploadControlsProps) {
  return (
    <div className="space-y-4">
      {selectedFileName ? <p className="text-sm text-zinc-400">Selected file: {selectedFileName}</p> : null}
      <div className="flex flex-wrap gap-3">
        <button className="button-primary" disabled={!canUpload || isUploading || isStartingTranscription} onClick={onUpload} type="button">
          {isUploading ? "Uploading audio..." : "Upload audio"}
        </button>
        <button className="button-primary" disabled={!canStartTranscription || isStartingTranscription || isUploading} onClick={onStartTranscription} type="button">
          Start transcription
        </button>
      </div>
    </div>
  );
}
