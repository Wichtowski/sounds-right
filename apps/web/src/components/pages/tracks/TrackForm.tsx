"use client";

type TrackFormProps = {
  artistId: string;
  title: string;
  album: string;
  artistOptions: Array<{ id: string; display_name: string }>;
  onArtistChange: (value: string) => void;
  onTitleChange: (value: string) => void;
  onAlbumChange: (value: string) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
  errorMessage?: string;
};

export function TrackForm({
  artistId,
  title,
  album,
  artistOptions,
  onArtistChange,
  onTitleChange,
  onAlbumChange,
  onSubmit,
  isSubmitting,
  errorMessage,
}: TrackFormProps) {
  return (
    <div className="space-y-5">
      <h1 className="text-3xl font-semibold">Tracks</h1>
      <form
        className="space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <select className="field" onChange={(event) => onArtistChange(event.target.value)} value={artistId}>
          <option value="">Choose artist</option>
          {artistOptions.map((artist) => (
            <option key={artist.id} value={artist.id}>
              {artist.display_name}
            </option>
          ))}
        </select>
        <input
          className="field"
          onChange={(event) => onTitleChange(event.target.value)}
          placeholder="Title"
          value={title}
        />
        <input
          className="field"
          onChange={(event) => onAlbumChange(event.target.value)}
          placeholder="Album"
          value={album}
        />
        <button className="button-primary" disabled={isSubmitting || !artistId} type="submit">
          Create track
        </button>
      </form>
      {errorMessage ? <p className="text-sm text-red-300">{errorMessage}</p> : null}
    </div>
  );
}
