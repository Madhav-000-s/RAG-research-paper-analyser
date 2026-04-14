"use client";

import { useState, useEffect, useRef } from "react";

interface PdfViewerProps {
  pdfUrl: string;
  highlightPage?: number;
  highlightSection?: string | null;
}

export default function PdfViewer({
  pdfUrl,
  highlightPage,
  highlightSection,
}: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);

  // Load PDF.js dynamically
  useEffect(() => {
    let cancelled = false;

    async function loadPdf() {
      try {
        const pdfjsLib = await import("pdfjs-dist");
        pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

        const doc = await pdfjsLib.getDocument(pdfUrl).promise;
        if (!cancelled) {
          setPdfDoc(doc);
          setNumPages(doc.numPages);
          setLoading(false);
        }
      } catch (err) {
        console.error("Failed to load PDF:", err);
        if (!cancelled) setLoading(false);
      }
    }

    loadPdf();
    return () => { cancelled = true; };
  }, [pdfUrl]);

  // Render current page
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current) return;

    let cancelled = false;

    async function renderPage() {
      const page = await pdfDoc.getPage(currentPage);
      const viewport = page.getViewport({ scale });
      const canvas = canvasRef.current!;
      const context = canvas.getContext("2d")!;

      canvas.height = viewport.height;
      canvas.width = viewport.width;

      await page.render({ canvasContext: context, viewport }).promise;
    }

    renderPage();
    return () => { cancelled = true; };
  }, [pdfDoc, currentPage, scale]);

  // Navigate to highlighted page when citation is clicked
  useEffect(() => {
    if (highlightPage && highlightPage > 0 && highlightPage <= numPages) {
      setCurrentPage(highlightPage);
    }
  }, [highlightPage, numPages]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-gray-500">Loading PDF...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage <= 1}
            className="px-2 py-1 text-sm border rounded disabled:opacity-50"
          >
            Prev
          </button>
          <span className="text-sm">
            Page {currentPage} of {numPages}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(numPages, p + 1))}
            disabled={currentPage >= numPages}
            className="px-2 py-1 text-sm border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setScale((s) => Math.max(0.5, s - 0.25))}
            className="px-2 py-1 text-sm border rounded"
          >
            -
          </button>
          <span className="text-sm">{Math.round(scale * 100)}%</span>
          <button
            onClick={() => setScale((s) => Math.min(3, s + 0.25))}
            className="px-2 py-1 text-sm border rounded"
          >
            +
          </button>
        </div>
      </div>

      {/* Citation banner */}
      {highlightPage === currentPage && highlightSection && (
        <div className="px-4 py-2 bg-yellow-50 border-b border-yellow-200 text-sm text-yellow-800">
          Source on this page — Section: {highlightSection}
        </div>
      )}

      {/* Canvas */}
      <div className="flex-1 overflow-auto flex justify-center p-4">
        <canvas ref={canvasRef} className="shadow-lg" />
      </div>
    </div>
  );
}
