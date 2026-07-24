"use client";

import React, { useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Download,
  Maximize2,
  FileText,
  AlertCircle,
} from "lucide-react";

interface DocumentViewerProps {
  documentId: string;
  filename: string;
  fileType?: "pdf" | "docx" | "txt";
  /** Optional highlight text excerpts */
  highlights?: { page: number; excerpt: string }[];
  onClose?: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DocumentViewer({
  documentId,
  filename,
  fileType = "pdf",
  highlights = [],
  onClose,
}: DocumentViewerProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages] = useState(1); // Updated via iframe messaging in production
  const [zoom, setZoom] = useState(100);
  const [loadError, setLoadError] = useState(false);

  const fileUrl = `${API_BASE}/api/v1/documents/${documentId}/download`;

  const incrementZoom = () => setZoom((z) => Math.min(z + 10, 200));
  const decrementZoom = () => setZoom((z) => Math.max(z - 10, 50));

  const handleDownload = async () => {
    const token = localStorage.getItem("paklaw_token");
    const res = await fetch(fileUrl, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full bg-background rounded-xl border border-border overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="h-4 w-4 text-primary shrink-0" />
          <span className="text-sm font-medium text-foreground truncate max-w-xs">{filename}</span>
        </div>

        <div className="flex items-center gap-1">
          {/* Page navigation */}
          {fileType === "pdf" && (
            <div className="flex items-center gap-1 mr-3 bg-muted rounded-lg px-2 py-1">
              <button
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                disabled={currentPage <= 1}
                className="disabled:opacity-40 hover:text-primary transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-xs font-medium text-foreground px-1">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                disabled={currentPage >= totalPages}
                className="disabled:opacity-40 hover:text-primary transition-colors"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Zoom controls */}
          <button
            onClick={decrementZoom}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <span className="text-xs font-medium text-foreground w-10 text-center">{zoom}%</span>
          <button
            onClick={incrementZoom}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
          >
            <ZoomIn className="h-4 w-4" />
          </button>

          {/* Actions */}
          <div className="h-5 w-px bg-border mx-1" />
          <button
            onClick={handleDownload}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
            title="Download"
          >
            <Download className="h-4 w-4" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
              title="Close viewer"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Document Preview Area */}
      <div className="flex-1 overflow-auto bg-muted/30 p-4 flex items-start justify-center">
        {loadError ? (
          <div className="flex flex-col items-center justify-center gap-3 text-muted-foreground py-20">
            <AlertCircle className="h-10 w-10 opacity-40" />
            <p className="text-sm">Unable to load document preview</p>
            <button
              onClick={handleDownload}
              className="text-xs text-primary hover:underline"
            >
              Download instead
            </button>
          </div>
        ) : fileType === "pdf" ? (
          <div
            className="shadow-lg rounded-lg overflow-hidden transition-all duration-200"
            style={{ width: `${zoom}%`, maxWidth: "960px" }}
          >
            <iframe
              src={`${fileUrl}#page=${currentPage}&toolbar=0&navpanes=0`}
              title={filename}
              className="w-full"
              style={{ height: "80vh" }}
              onError={() => setLoadError(true)}
            />
          </div>
        ) : (
          <div className="bg-card border border-border rounded-xl p-8 shadow-sm w-full max-w-3xl text-sm text-foreground leading-relaxed">
            <p className="text-muted-foreground italic text-xs mb-4">
              Text preview — download for full formatting
            </p>
            <pre className="whitespace-pre-wrap font-sans">
              [Document content will appear here when loaded from API]
            </pre>
          </div>
        )}
      </div>

      {/* Highlights Bar */}
      {highlights.length > 0 && (
        <div className="border-t border-border bg-card px-4 py-2 shrink-0">
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Relevant Excerpts
          </p>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {highlights.map((h, i) => (
              <button
                key={i}
                onClick={() => setCurrentPage(h.page)}
                className="shrink-0 text-xs bg-primary/10 text-primary border border-primary/20 rounded-lg px-3 py-1.5 hover:bg-primary/20 transition-all"
              >
                Page {h.page}: &ldquo;{h.excerpt.slice(0, 40)}…&rdquo;
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
