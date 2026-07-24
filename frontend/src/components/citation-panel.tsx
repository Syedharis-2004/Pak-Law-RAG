"use client";

import React from "react";
import { X, ExternalLink, FileText, ChevronRight } from "lucide-react";
import { truncate } from "@/lib/utils";

export interface Citation {
  id: string;
  citation_number: number;
  document_title: string;
  document_id?: string;
  section_number?: string;
  section_title?: string;
  page_number?: number;
  excerpt?: string;
  relevance_score?: number;
}

interface CitationPanelProps {
  citations: Citation[];
  onClose: () => void;
}

export default function CitationPanel({ citations, onClose }: CitationPanelProps) {
  return (
    <aside className="w-80 border-l border-border bg-card h-full flex flex-col">
      {/* Header */}
      <div className="h-16 border-b border-border px-5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-primary" />
          <h3 className="font-semibold text-sm text-foreground">
            Source Citations
            <span className="ml-2 text-xs font-normal text-muted-foreground">
              ({citations.length})
            </span>
          </h3>
        </div>
        <button
          onClick={onClose}
          aria-label="Close citations panel"
          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Citation List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {citations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground gap-2 py-12">
            <FileText className="h-8 w-8 opacity-30" />
            <p className="text-sm">No citations available</p>
          </div>
        ) : (
          citations.map((cit) => (
            <CitationCard key={cit.id} citation={cit} />
          ))
        )}
      </div>
    </aside>
  );
}

function CitationCard({ citation: cit }: { citation: Citation }) {
  return (
    <div className="group bg-background border border-border rounded-xl p-4 space-y-2.5 hover:border-primary/30 transition-all hover:shadow-sm">
      {/* Citation number + document title */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="shrink-0 h-5 w-5 rounded-full bg-primary/10 text-primary text-[10px] font-bold flex items-center justify-center">
            {cit.citation_number}
          </span>
          <span className="text-xs font-semibold text-foreground truncate" title={cit.document_title}>
            {cit.document_title}
          </span>
        </div>
        {cit.relevance_score !== undefined && (
          <span
            className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
              cit.relevance_score >= 0.8
                ? "bg-emerald-500/10 text-emerald-600"
                : cit.relevance_score >= 0.5
                ? "bg-amber-500/10 text-amber-600"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {Math.round(cit.relevance_score * 100)}% match
          </span>
        )}
      </div>

      {/* Section info */}
      {cit.section_number && (
        <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
          <ChevronRight className="h-3 w-3 shrink-0" />
          <span className="font-medium">§{cit.section_number}</span>
          {cit.section_title && (
            <span className="truncate">&nbsp;— {cit.section_title}</span>
          )}
        </div>
      )}

      {/* Page number */}
      {cit.page_number && (
        <p className="text-[11px] text-muted-foreground">Page {cit.page_number}</p>
      )}

      {/* Excerpt */}
      {cit.excerpt && (
        <blockquote className="text-xs text-muted-foreground border-l-2 border-primary/30 pl-3 italic leading-relaxed">
          &ldquo;{truncate(cit.excerpt, 200)}&rdquo;
        </blockquote>
      )}

      {/* View in document link */}
      {cit.document_id && (
        <a
          href={`/documents/${cit.document_id}`}
          className="flex items-center gap-1 text-[11px] text-primary hover:underline mt-1 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <ExternalLink className="h-3 w-3" />
          Open in Document Viewer
        </a>
      )}
    </div>
  );
}
