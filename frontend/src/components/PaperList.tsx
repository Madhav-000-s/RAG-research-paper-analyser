"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchPapers } from "@/lib/api";
import type { Paper } from "@/lib/types";

export default function PaperList() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchPapers();
        if (!cancelled) setPapers(data);
      } catch (err) {
        console.error("Failed to fetch papers:", err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    // Poll for status updates every 5 seconds
    const interval = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return <p className="text-gray-500">Loading papers...</p>;
  }

  if (papers.length === 0) {
    return <p className="text-gray-500">No papers uploaded yet.</p>;
  }

  return (
    <div className="space-y-3">
      {papers.map((paper) => (
        <div
          key={paper.id}
          className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 shadow-sm"
        >
          <div className="flex-1 min-w-0">
            <h3 className="font-medium truncate">
              {paper.title || paper.filename}
            </h3>
            {paper.authors && paper.authors.length > 0 && (
              <p className="text-sm text-gray-500 truncate">
                {paper.authors.join(", ")}
              </p>
            )}
            <p className="text-xs text-gray-400">
              {paper.page_count ? `${paper.page_count} pages` : ""}{" "}
              {paper.chunk_count ? `· ${paper.chunk_count} chunks` : ""}
            </p>
          </div>

          <div className="flex items-center gap-3 ml-4">
            <StatusBadge status={paper.status} />
            {paper.status === "ready" && (
              <Link
                href={`/papers/${paper.id}`}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Ask Questions
              </Link>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    processing: "bg-yellow-100 text-yellow-800",
    ready: "bg-green-100 text-green-800",
    error: "bg-red-100 text-red-800",
  };

  return (
    <span
      className={`px-2 py-0.5 text-xs font-medium rounded-full ${
        styles[status] || "bg-gray-100 text-gray-800"
      }`}
    >
      {status}
    </span>
  );
}
