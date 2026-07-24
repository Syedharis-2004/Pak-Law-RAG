"use client";

import React, { useState } from "react";
import {
  FileText,
  Download,
  Clock,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  BookOpen,
  Calendar,
  Scale,
} from "lucide-react";
import { formatDate } from "@/lib/utils";

interface ResearchSection {
  section_title: string;
  content: string;
  citations?: { citation_number: number; document_title: string; excerpt?: string }[];
}

interface ResearchReport {
  id: string;
  title: string;
  query: string;
  status: "pending" | "processing" | "completed" | "failed";
  jurisdiction?: string;
  language: string;
  created_at: string;
  completed_at?: string;
  executive_summary?: string;
  sections?: ResearchSection[];
  total_sources?: number;
  word_count?: number;
}

interface ResearchReportViewerProps {
  report: ResearchReport;
  onDownload?: () => void;
}

export default function ResearchReportViewer({ report, onDownload }: ResearchReportViewerProps) {
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set([0]));

  const toggleSection = (idx: number) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  if (report.status === "pending" || report.status === "processing") {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4 text-muted-foreground">
        <div className="relative">
          <div className="h-16 w-16 rounded-full border-2 border-primary/20 animate-pulse" />
          <Loader2 className="h-8 w-8 text-primary animate-spin absolute inset-0 m-auto" />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-foreground">Generating Legal Research Report</p>
          <p className="text-xs mt-1">
            {report.status === "pending" ? "Queued for processing…" : "Analyzing case law and statutes…"}
          </p>
        </div>
        <div className="w-48 h-1.5 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full animate-pulse w-2/3" />
        </div>
      </div>
    );
  }

  if (report.status === "failed") {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3 text-muted-foreground">
        <AlertTriangle className="h-10 w-10 text-destructive opacity-60" />
        <p className="text-sm font-medium text-foreground">Report Generation Failed</p>
        <p className="text-xs">Please try generating the report again</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      {/* Report Header */}
      <div className="bg-gradient-to-br from-primary/5 to-primary/10 border-b border-border px-8 py-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Scale className="h-4 w-4 text-primary" />
              <span className="text-xs font-semibold text-primary uppercase tracking-wider">
                Legal Research Report
              </span>
            </div>
            <h2 className="text-xl font-bold text-foreground leading-snug">{report.title}</h2>

            <div className="flex flex-wrap gap-4 mt-3 text-xs text-muted-foreground">
              {report.jurisdiction && (
                <span className="flex items-center gap-1">
                  <BookOpen className="h-3.5 w-3.5" />
                  {report.jurisdiction}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {formatDate(report.created_at)}
              </span>
              {report.total_sources !== undefined && (
                <span className="flex items-center gap-1">
                  <FileText className="h-3.5 w-3.5" />
                  {report.total_sources} sources
                </span>
              )}
              {report.word_count !== undefined && (
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5" />
                  ~{report.word_count.toLocaleString()} words
                </span>
              )}
            </div>
          </div>

          {onDownload && (
            <button
              onClick={onDownload}
              className="shrink-0 flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary/90 transition-all"
            >
              <Download className="h-4 w-4" />
              Export PDF
            </button>
          )}
        </div>

        {/* Status badge */}
        <div className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-emerald-600 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Completed
        </div>
      </div>

      <div className="p-8 space-y-6">
        {/* Executive Summary */}
        {report.executive_summary && (
          <div className="bg-muted/40 border border-border rounded-xl p-6">
            <h3 className="text-sm font-bold text-foreground mb-3 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              Executive Summary
            </h3>
            <p className="text-sm text-foreground leading-relaxed">{report.executive_summary}</p>
          </div>
        )}

        {/* Research Sections */}
        {report.sections && report.sections.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
              Analysis Sections
            </h3>
            {report.sections.map((section, idx) => (
              <div
                key={idx}
                className="border border-border rounded-xl overflow-hidden hover:border-primary/20 transition-colors"
              >
                <button
                  onClick={() => toggleSection(idx)}
                  className="w-full flex items-center justify-between px-5 py-4 bg-card hover:bg-muted/30 transition-colors"
                >
                  <span className="font-semibold text-sm text-foreground text-left">
                    {idx + 1}. {section.section_title}
                  </span>
                  {expandedSections.has(idx) ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                  )}
                </button>

                {expandedSections.has(idx) && (
                  <div className="px-5 pb-5 pt-2 border-t border-border">
                    <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                      {section.content}
                    </p>

                    {/* Inline citations */}
                    {section.citations && section.citations.length > 0 && (
                      <div className="mt-4 space-y-2">
                        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                          Sources
                        </p>
                        {section.citations.map((cit, ci) => (
                          <div key={ci} className="flex gap-2 text-xs text-muted-foreground">
                            <span className="text-primary font-bold shrink-0">[{cit.citation_number}]</span>
                            <span>
                              <span className="font-medium text-foreground">{cit.document_title}</span>
                              {cit.excerpt && <span> — &ldquo;{cit.excerpt}&rdquo;</span>}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
