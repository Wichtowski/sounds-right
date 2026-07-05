"use client";

import { useEffect, useState } from "react";

import { api } from "@lib/api";

type ApiStatus = "loading" | "ok" | "error";

export function ApiStatusBadge() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("loading");

  useEffect(() => {
    const controller = new AbortController();

    api.health({ signal: controller.signal })
      .then((body) => {
        setApiStatus(body.status === "ok" ? "ok" : "error");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }

        setApiStatus("error");
      });

    return () => controller.abort();
  }, []);

  return (
    <div className="inline-flex items-center gap-3 rounded border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm">
      <span className="h-2.5 w-2.5 rounded-full bg-cyan-300" aria-hidden="true" />
      <span className="font-medium text-zinc-200">API status:</span>
      <span className="text-zinc-300">{apiStatus}</span>
    </div>
  );
}
