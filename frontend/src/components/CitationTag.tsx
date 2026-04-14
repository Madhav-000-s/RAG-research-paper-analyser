"use client";

import type { Citation } from "@/lib/types";

interface CitationTagProps {
  number: number;
  citation: Citation;
  onClick: (citation: Citation) => void;
}

export default function CitationTag({
  number,
  citation,
  onClick,
}: CitationTagProps) {
  return (
    <button
      onClick={() => onClick(citation)}
      className="inline-flex items-center justify-center min-w-[1.5rem] h-5 px-1 mx-0.5 text-xs font-semibold text-blue-700 bg-blue-100 rounded hover:bg-blue-200 transition-colors cursor-pointer align-super"
      title={`Page ${citation.page_number}${
        citation.section_heading ? `, ${citation.section_heading}` : ""
      }: ${citation.snippet.slice(0, 100)}...`}
    >
      {number}
    </button>
  );
}
