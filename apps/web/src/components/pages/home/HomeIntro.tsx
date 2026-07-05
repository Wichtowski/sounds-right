type HomeIntroProps = {
  registerHref: string;
  artistsHref: string;
};

export function HomeIntro({ registerHref, artistsHref }: HomeIntroProps) {
  return (
    <div className="space-y-6">
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-300">Sounds Right</p>
      <h1 className="max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
        Core catalog and upload workflow
      </h1>
      <p className="max-w-2xl text-lg leading-8 text-zinc-300">
        Register, create artists and tracks, create a version, then upload temporary audio directly to MinIO.
      </p>
      <div className="flex flex-wrap gap-3">
        <a className="rounded-md bg-cyan-300 px-4 py-2 text-sm font-semibold text-zinc-950" href={registerHref}>
          Register
        </a>
        <a className="rounded-md border border-zinc-700 px-4 py-2 text-sm font-semibold text-zinc-100" href={artistsHref}>
          Manage artists
        </a>
      </div>
    </div>
  );
}
