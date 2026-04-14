"use client";

import { useCallback, useState } from "react";
import { uploadPaper } from "@/lib/api";

interface PaperUploadProps {
  onUploadComplete: () => void;
}

export default function PaperUpload({ onUploadComplete }: PaperUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Only PDF files are accepted");
        return;
      }

      setUploading(true);
      setError(null);

      try {
        await uploadPaper(file);
        onUploadComplete();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [onUploadComplete]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        isDragging
          ? "border-blue-500 bg-blue-50"
          : "border-gray-300 hover:border-gray-400"
      }`}
    >
      {uploading ? (
        <div className="flex items-center justify-center gap-2">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-600">Uploading and processing...</span>
        </div>
      ) : (
        <>
          <p className="text-gray-600 mb-2">
            Drag and drop a PDF here, or click to browse
          </p>
          <label className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md cursor-pointer hover:bg-blue-700 transition-colors">
            Choose PDF
            <input
              type="file"
              accept=".pdf"
              onChange={handleInputChange}
              className="hidden"
            />
          </label>
        </>
      )}
      {error && <p className="mt-2 text-red-600 text-sm">{error}</p>}
    </div>
  );
}
