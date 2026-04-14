"use client";

import { useState } from "react";
import PaperUpload from "@/components/PaperUpload";
import PaperList from "@/components/PaperList";

export default function HomePage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">RAG Paper Intelligence</h1>
      <p className="text-gray-600 mb-8">
        Upload research papers, ask questions, and get answers with inline
        citations.
      </p>

      <PaperUpload onUploadComplete={() => setRefreshKey((k) => k + 1)} />

      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Your Papers</h2>
        <PaperList key={refreshKey} />
      </div>
    </main>
  );
}
