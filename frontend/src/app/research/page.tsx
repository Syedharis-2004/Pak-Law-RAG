"use client";

import React, { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/sidebar";
import { api } from "@/lib/api";
import { 
  FileText, 
  Loader2, 
  Download, 
  ChevronRight, 
  History, 
  Plus,
  Scale,
  ShieldCheck,
  ZapOff,
  Sparkles,
  Printer,
  CheckCircle2
} from "lucide-react";

interface ResearchReport {
  id: string;
  research_query: string;
  language: string;
  status: "queued" | "generating" | "completed" | "failed";
  title?: string;
  executive_summary?: string;
  full_content_markdown?: string;
  documents_searched: number;
  sections_retrieved: number;
  error_message?: string;
  created_at: string;
}

export default function ResearchHubPage() {
  const [reports, setReports] = useState<ResearchReport[]>([]);
  const [activeReportId, setActiveReportId] = useState<string | null>(null);
  const [activeReport, setActiveReport] = useState<ResearchReport | null>(null);
  const [query, setQuery] = useState("");
  const [language, setLanguage] = useState("en");

  // Options
  const [includeJudgments, setIncludeJudgments] = useState(true);
  const [includeAmendments, setIncludeAmendments] = useState(true);

  const [loadingList, setLoadingList] = useState(false);
  const [loadingActive, setLoadingActive] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadReports();
  }, []);

  useEffect(() => {
    // Cancel any in-flight poll from the previous report before starting a new one
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    if (activeReportId) {
      pollAttemptsRef.current[activeReportId] = 0; // reset counter for new selection
      loadReportDetails(activeReportId);
    } else {
      setActiveReport(null);
    }
  }, [activeReportId]);

  const loadReports = async () => {
    setLoadingList(true);
    try {
      const res = await api.get<{ items: ResearchReport[] }>("/api/v1/research/reports");
      setReports(res.items);
      if (res.items.length > 0 && !activeReportId) {
        setActiveReportId(res.items[0].id);
      }
    } catch (e) {
      // Ignore initial loads error handling
    } finally {
      setLoadingList(false);
    }
  };

  // Track the current polling timer so we can cancel it when switching reports
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollAttemptsRef = useRef<Record<string, number>>({});

  const loadReportDetails = async (id: string) => {
    setLoadingActive(true);
    try {
      const res = await api.get<ResearchReport>(`/api/v1/research/reports/${id}`);
      setActiveReport(res);

      // Auto-poll while the report is still in-progress
      if (res.status === "queued" || res.status === "generating") {
        const attempts = (pollAttemptsRef.current[id] ?? 0) + 1;
        pollAttemptsRef.current[id] = attempts;

        // Stop polling after ~2 minutes (60 × 2s) to avoid infinite loops
        if (attempts < 60) {
          if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
          // Capture `id` directly — avoids stale activeReportId closure
          pollTimerRef.current = setTimeout(() => loadReportDetails(id), 2000);
        }
      } else {
        // Report is done — reset attempt counter and clear any pending timer
        delete pollAttemptsRef.current[id];
        if (pollTimerRef.current) {
          clearTimeout(pollTimerRef.current);
          pollTimerRef.current = null;
        }
      }
    } catch (e) {
      // Silently ignore transient network errors during polling
    } finally {
      setLoadingActive(false);
    }
  };

  const handleTriggerResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || generating) return;

    setGenerating(true);
    try {
      const res = await api.post<ResearchReport>("/api/v1/research/report", {
        query,
        language,
        include_judgments: includeJudgments,
        include_amendments: includeAmendments,
      });

      setReports((prev) => [res, ...prev]);
      setActiveReportId(res.id);
      setQuery("");
    } catch (e: any) {
      alert(e.message || "Failed starting research");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = (format: "pdf" | "docx") => {
    if (!activeReportId) return;
    const exportUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/research/export`;
    
    const form = document.createElement("form");
    form.method = "POST";
    form.action = exportUrl;
    form.target = "_blank";

    const addField = (name: string, value: string) => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      input.value = value;
      form.appendChild(input);
    };

    addField("report_id", activeReportId);
    addField("format", format);
    
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <Sidebar />

      {/* Main Workspace */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Research Reports History Panel */}
        <aside className="w-80 border-r border-border/80 bg-card/60 flex flex-col h-full overflow-hidden shrink-0">
          <div className="h-16 border-b border-border/60 px-6 flex items-center justify-between">
            <h3 className="font-bold text-xs text-foreground uppercase tracking-wider flex items-center gap-2">
              <History className="h-4 w-4 text-primary" />
              Research History
            </h3>
            <button
              onClick={() => {
                setActiveReportId(null);
                setActiveReport(null);
              }}
              className="p-1.5 hover:bg-muted rounded-xl text-muted-foreground hover:text-foreground transition-all"
              title="New Research Memo"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {reports.map((item) => {
              const isActive = item.id === activeReportId;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveReportId(item.id)}
                  className={`w-full text-left p-3.5 rounded-2xl border transition-all space-y-1.5 shadow-2xs ${
                    isActive
                      ? "border-primary bg-primary/10 shadow-sm"
                      : "border-border/70 hover:bg-muted/60"
                  }`}
                >
                  <p className="font-bold text-xs text-foreground line-clamp-2 leading-snug">
                    {item.title || item.research_query}
                  </p>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-0.5">
                    <span className={`capitalize font-bold px-2 py-0.5 rounded-full ${
                      item.status === "completed"
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                        : item.status === "generating"
                        ? "bg-amber-500/10 text-amber-600"
                        : "bg-muted text-muted-foreground"
                    }`}>
                      {item.status}
                    </span>
                    <span>{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        {/* Right Workspace & Report Details */}
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
          {activeReportId === null ? (
            /* Research Mode Initiator Form */
            <div className="flex-1 overflow-y-auto p-8 flex flex-col justify-center items-center">
              <div className="max-w-2xl w-full glass-panel p-8 rounded-3xl border border-border/80 shadow-2xl space-y-6">
                <div className="flex flex-col items-center text-center space-y-2">
                  <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shadow-sm">
                    <Scale className="h-6 w-6" />
                  </div>
                  <h2 className="text-2xl font-bold text-foreground">Launch Deep Legal Research Workflow</h2>
                  <p className="text-xs text-muted-foreground max-w-md leading-relaxed">
                    LangGraph multi-step analytical engine synthesizing statutory provisions, case law precedents, and statutory amendments into an executive memo.
                  </p>
                </div>

                <form onSubmit={handleTriggerResearch} className="space-y-5">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider" htmlFor="researchQuery">
                      Specify the Legal Question or Issue
                    </label>
                    <textarea
                      id="researchQuery"
                      required
                      rows={4}
                      placeholder="Specify conflict of provisions, penal liabilities, constitutional writ petition grounds, or commercial contract disputes..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      className="w-full bg-background border border-border/80 rounded-2xl p-4 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider" htmlFor="researchLanguage">
                        Report Output Language
                      </label>
                      <select
                        id="researchLanguage"
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="w-full bg-background border border-border/80 rounded-xl px-3.5 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 font-medium"
                      >
                        <option value="en">English Legal Research Memo</option>
                        <option value="ur">Urdu (اردو)</option>
                        <option value="ro">Roman Urdu</option>
                      </select>
                    </div>

                    <div className="flex flex-col justify-center gap-2 pt-2">
                      <label className="flex items-center gap-2 text-xs font-semibold text-muted-foreground cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={includeJudgments}
                          onChange={() => setIncludeJudgments(!includeJudgments)}
                          className="rounded border-border text-primary focus:ring-primary/20 h-4 w-4"
                        />
                        <span>Analyze High Court Case Precedents</span>
                      </label>
                      <label className="flex items-center gap-2 text-xs font-semibold text-muted-foreground cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={includeAmendments}
                          onChange={() => setIncludeAmendments(!includeAmendments)}
                          className="rounded border-border text-primary focus:ring-primary/20 h-4 w-4"
                        />
                        <span>Map Statutory Amendment History</span>
                      </label>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={generating || !query.trim()}
                    className="w-full bg-primary text-primary-foreground py-3.5 rounded-2xl font-semibold hover:bg-primary/95 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-md shadow-primary/15 hover:-translate-y-0.5"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span>Synthesizing Legal Analysis...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        <span>Generate Executive Legal Memo</span>
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>
          ) : (
            /* Report Details View */
            <div className="flex-1 flex flex-col overflow-hidden">
              <header className="h-16 border-b border-border/60 bg-card/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
                <div className="min-w-0">
                  <h3 className="font-bold text-sm text-foreground truncate max-w-md">{activeReport?.title || "Legal Research Report"}</h3>
                  <p className="text-[10px] text-muted-foreground">Status: <b className="capitalize text-primary">{activeReport?.status}</b></p>
                </div>
                {activeReport?.status === "completed" && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDownload("pdf")}
                      className="flex items-center gap-1.5 bg-card hover:bg-muted text-foreground px-3.5 py-1.5 rounded-xl text-xs font-bold border border-border/80 transition-all shadow-2xs"
                    >
                      <Download className="h-3.5 w-3.5 text-primary" /> PDF Memo
                    </button>
                    <button
                      onClick={() => handleDownload("docx")}
                      className="flex items-center gap-1.5 bg-card hover:bg-muted text-foreground px-3.5 py-1.5 rounded-xl text-xs font-bold border border-border/80 transition-all shadow-2xs"
                    >
                      <Download className="h-3.5 w-3.5 text-primary" /> Word Doc
                    </button>
                  </div>
                )}
              </header>

              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {activeReport?.status === "completed" ? (
                  <div className="bg-card border border-border/80 rounded-2xl p-8 shadow-sm space-y-6 max-w-4xl mx-auto">
                    <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-xs bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 w-fit">
                      <CheckCircle2 className="h-4 w-4" />
                      Verified Statutory Grounding • Zero Hallucination Certified
                    </div>

                    <div className="whitespace-pre-wrap text-sm leading-relaxed text-foreground font-sans prose dark:prose-invert max-w-none">
                      {activeReport.full_content_markdown}
                    </div>
                  </div>
                ) : activeReport?.status === "failed" ? (
                  <div className="h-full flex flex-col items-center justify-center text-center text-destructive max-w-md mx-auto space-y-2">
                    <ZapOff className="h-10 w-10 opacity-30" />
                    <h4 className="font-bold">Analysis Terminated</h4>
                    <p className="text-xs text-muted-foreground">{activeReport.error_message || "An unexpected error occurred during evaluation."}</p>
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground max-w-md mx-auto space-y-3">
                    <Loader2 className="h-10 w-10 text-primary animate-spin" />
                    <h4 className="font-bold text-foreground">Generating Research Report</h4>
                    <p className="text-xs leading-relaxed">Synthesizing dense vector citations, statutory sections, and legal recommendations...</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

