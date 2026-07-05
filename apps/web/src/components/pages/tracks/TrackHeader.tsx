"use client";

type TrackHeaderProps = {
  title: string;
  artistName?: string;
  onCreateVersion: () => void;
  isSubmitting: boolean;
  errorMessage?: string;
};

export function TrackHeader({
  title,
  artistName,
  onCreateVersion,
  isSubmitting,
  errorMessage,
}: TrackHeaderProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">{title}</h1>
          <p className="text-sm text-zinc-400">{artistName}</p>
        </div>
        <button className="button-primary" disabled={isSubmitting} onClick={onCreateVersion}>
          Create version
        </button>
      </div>
      {errorMessage ? <p className="text-sm text-red-300">{errorMessage}</p> : null}
    </div>
  );
}
