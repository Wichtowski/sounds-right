"use client";

type ArtistFormProps = {
  displayName: string;
  fullName: string;
  onDisplayNameChange: (value: string) => void;
  onFullNameChange: (value: string) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
  errorMessage?: string;
};

export function ArtistForm({
  displayName,
  fullName,
  onDisplayNameChange,
  onFullNameChange,
  onSubmit,
  isSubmitting,
  errorMessage,
}: ArtistFormProps) {
  return (
    <div className="space-y-5">
      <h1 className="text-3xl font-semibold">Artists</h1>
      <form
        className="space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <input
          className="field"
          onChange={(event) => onDisplayNameChange(event.target.value)}
          placeholder="Display name"
          value={displayName}
        />
        <input
          className="field"
          onChange={(event) => onFullNameChange(event.target.value)}
          placeholder="Full name"
          value={fullName}
        />
        <button className="button-primary" disabled={isSubmitting} type="submit">
          Create artist
        </button>
      </form>
      {errorMessage ? <p className="text-sm text-red-300">{errorMessage}</p> : null}
    </div>
  );
}
