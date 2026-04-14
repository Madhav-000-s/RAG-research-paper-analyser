"use client";

import type { Citation } from "@/lib/types";
import CitationTag from "./CitationTag";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  onCitationClick: (citation: Citation) => void;
}

export default function MessageBubble({
  role,
  content,
  citations = [],
  onCitationClick,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-white border border-gray-200 text-gray-800"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : (
          <div className="whitespace-pre-wrap leading-relaxed">
            {renderWithCitations(content, citations, onCitationClick)}
          </div>
        )}

        {!isUser && citations.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-1">Sources:</p>
            <div className="space-y-1">
              {citations.map((c, i) => (
                <button
                  key={c.chunk_id}
                  onClick={() => onCitationClick(c)}
                  className="block w-full text-left text-xs text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded px-2 py-1 transition-colors"
                >
                  <span className="font-semibold">[{i + 1}]</span> Page{" "}
                  {c.page_number}
                  {c.section_heading && ` - ${c.section_heading}`}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function renderWithCitations(
  text: string,
  citations: Citation[],
  onCitationClick: (citation: Citation) => void
): React.ReactNode[] {
  // Split text on citation patterns like [1], [2], etc.
  const parts = text.split(/(\[\d+\])/g);

  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) {
      const num = parseInt(match[1], 10);
      const citation = citations.find(
        (_, idx) => idx === num - 1
      );
      if (citation) {
        return (
          <CitationTag
            key={i}
            number={num}
            citation={citation}
            onClick={onCitationClick}
          />
        );
      }
    }
    return <span key={i}>{part}</span>;
  });
}
