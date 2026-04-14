"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchPaper, getPaperPdfUrl } from "@/lib/api";
import type { Citation, Paper } from "@/lib/types";
import PdfViewer from "@/components/PdfViewer";
import ChatPanel from "@/components/ChatPanel";

export default function PaperDetailPage() {
  const params = useParams();
  const paperId = params.id as string;

  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchPaper(paperId);
        setPaper(data);
      } catch (err) {
        console.error("Failed to load paper:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [paperId]);

  const handleCitationClick = (citation: Citation) => {
    setActiveCitation(citation);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-500">Paper not found</p>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="px-4 py-3 bg-white border-b border-gray-200 flex items-center justify-between">
        <div className="min-w-0">
          <h1 className="text-lg font-semibold truncate">
            {paper.title || paper.filename}
          </h1>
          {paper.authors && (
            <p className="text-sm text-gray-500 truncate">
              {paper.authors.join(", ")}
            </p>
          )}
        </div>
        <a
          href="/"
          className="text-sm text-blue-600 hover:text-blue-800 ml-4 whitespace-nowrap"
        >
          Back to Papers
        </a>
      </header>

      {/* Split pane: PDF viewer | Chat */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: PDF viewer */}
        <div className="w-1/2 border-r border-gray-200">
          <PdfViewer
            pdfUrl={getPaperPdfUrl(paperId)}
            highlightPage={activeCitation?.page_number}
            highlightSection={activeCitation?.section_heading}
          />
        </div>

        {/* Right: Chat panel */}
        <div className="w-1/2">
          <ChatPanel
            paperId={paperId}
            onCitationClick={handleCitationClick}
          />
        </div>
      </div>
    </div>
  );
}
