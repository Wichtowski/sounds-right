"use client";

type VersionHeaderProps = {
  version: string | number | "";
  status: string;
};

export function VersionHeader({ version, status }: VersionHeaderProps) {
  return (
    <div>
      <h1 className="text-3xl font-semibold">Version {version}</h1>
      <p className="text-sm text-zinc-400">Status: {status}</p>
    </div>
  );
}
