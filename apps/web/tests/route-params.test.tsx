import { expect, test } from "bun:test";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToReadableStream } from "react-dom/server";

import JobPage from "../src/app/jobs/[jobId]/page";
import KaraokePage from "../src/app/karaoke/[artistSlug]/[trackSlug]/page";
import TrackPage from "../src/app/tracks/[trackId]/page";
import VersionPage from "../src/app/versions/[versionId]/page";
import ReviewPage from "../src/app/versions/[versionId]/review/page";

const cases = [
  {
    name: "track",
    page: <TrackPage params={Promise.resolve({ trackId: "track-id" })} />,
    queryKey: ["track", "track-id"],
    data: { title: "Route track fixture" },
    expected: "Route track fixture",
  },
  {
    name: "version",
    page: <VersionPage params={Promise.resolve({ versionId: "version-id" })} />,
    queryKey: ["version", "version-id"],
    data: { version: 42, status: "uploaded" },
    expected: "Version 42",
  },
  {
    name: "review",
    page: <ReviewPage params={Promise.resolve({ versionId: "version-id" })} />,
    queryKey: ["version", "version-id"],
    data: { version: 42, status: "rejected" },
    expected: "Version 42 review",
  },
  {
    name: "job",
    page: <JobPage params={Promise.resolve({ jobId: "route-job-id" })} />,
    queryKey: ["job", "route-job-id"],
    data: { status: "processing" },
    expected: "route-job-id",
  },
  {
    name: "public karaoke",
    page: <KaraokePage params={Promise.resolve({ artistSlug: "artist-slug", trackSlug: "track-slug" })} />,
    queryKey: ["public-karaoke-latest", "artist-slug", "track-slug"],
    data: { manifest: { artist: { display_name: "Artist fixture" }, track: { title: "Song fixture" } } },
    expected: "Artist fixture - Song fixture",
  },
];

for (const scenario of cases) {
  test(`${scenario.name} resolves promised route params before reading page data`, async () => {
    const client = new QueryClient();
    client.setQueryData(scenario.queryKey, scenario.data);
    try {
      const stream = await renderToReadableStream(
        <QueryClientProvider client={client}>{scenario.page}</QueryClientProvider>,
      );
      const html = await new Response(stream).text();
      expect(html.replace(/<!--.*?-->/g, "")).toContain(scenario.expected);
    } finally {
      client.clear();
    }
  });
}
