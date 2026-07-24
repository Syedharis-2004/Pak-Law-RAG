"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  X,
  Loader2,
  FileText,
  ChevronDown,
  SlidersHorizontal,
  BookOpen,
  Sparkles,
  Copy,
  Check,
  ExternalLink,
  Tag
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDate, truncate } from "@/lib/utils";
import { debounce } from "@/lib/utils";

interface SearchResult {
  document_id: string;
  document_title: string;
  document_type?: string;
  section_number?: string;
  section_title?: string;
  content: string;
  score: number;
  page_number?: number;
  year?: number;
}

interface SearchFilters {
  document_type?: string;
  year_from?: number;
  year_to?: number;
  language?: string;
}

export default function SearchInterface() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<SearchFilters>({});
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const DOC_TYPES = ["Act", "Ordinance", "Judgment", "Contract", "Regulation", "Amendment", "Constitution"];
  const POPULAR_SEARCHES = [
    "Constitution Article 199",
    "CPC Order 39 Injunction",
    "PPC Section 302 Penalties",
    "CrPC 497 Bail Grounds",
    "Income Tax Ordinance 2001",
    "Contract Act Breach Notice"
  ];

  const performSearch = async (q: string, f: SearchFilters, p: number) => {
    if (!q.trim()) {
      setResults([]);
      setTotal(0);
      return;
    }
    setLoading(true);
    try {
      const res = await api.post<{ results: SearchResult[]; total: number }>(
        "/api/v1/search",
        {
          query: q,
          document_types: f.document_type ? [f.document_type.toLowerCase()] : undefined,
          languages: f.language ? [f.language] : undefined,
          page: p,
          page_size: 10,
          top_k: 30,
          search_type: "hybrid",
        }
      );
      setResults(res.results);
      setTotal(res.total);
    } catch (e) {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const debouncedSearch = debounce(performSearch, 400);

  useEffect(() => {
    debouncedSearch(query, filters, page);
  }, [query, filters, page]);

  const clearFilters = () => {
    setFilters({});
    setPage(1);
  };

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="flex flex-col h-full gap-5">
      {/* Search Input Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setPage(1); }}
            placeholder="Search Pakistan Acts, CPC/PPC Sections, High Court Judgments, Contract clauses..."
            className="w-full pl-11 pr-10 py-3.5 bg-background border border-border/80 rounded-2xl text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all shadow-xs"
            autoFocus
          />
          {query && (
            <button
              onClick={() => { setQuery(""); setResults([]); }}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1 rounded-md"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowFilters((v) => !v)}
          className={`flex items-center gap-2 px-4 py-3.5 rounded-2xl border text-sm font-semibold transition-all shadow-xs ${
            showFilters || activeFilterCount > 0
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-card border-border/80 text-foreground hover:border-primary/50"
          }`}
        >
          <SlidersHorizontal className="h-4 w-4" />
          <span>Filters</span>
          {activeFilterCount > 0 && (
            <span className="bg-primary-foreground text-primary text-xs font-bold rounded-full px-1.5 py-0.5">
              {activeFilterCount}
            </span>
          )}
        </button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-card border border-border/80 rounded-2xl p-4 flex flex-wrap gap-4 items-end shadow-sm animate-in slide-in-from-top-2 duration-200">
          {/* Document Type */}
          <div className="flex flex-col gap-1.5 min-w-[160px]">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Statute Classification</label>
            <select
              value={filters.document_type || ""}
              onChange={(e) => setFilters((f) => ({ ...f, document_type: e.target.value || undefined }))}
              className="bg-background border border-border/80 rounded-xl px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">All Categories</option>
              {DOC_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>

          {/* Year From */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Year From</label>
            <input
              type="number"
              min={1860}
              max={2026}
              value={filters.year_from || ""}
              onChange={(e) => setFilters((f) => ({ ...f, year_from: e.target.value ? +e.target.value : undefined }))}
              placeholder="e.g. 1973"
              className="bg-background border border-border/80 rounded-xl px-3 py-2 text-sm text-foreground w-28 focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {/* Year To */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Year To</label>
            <input
              type="number"
              min={1860}
              max={2026}
              value={filters.year_to || ""}
              onChange={(e) => setFilters((f) => ({ ...f, year_to: e.target.value ? +e.target.value : undefined }))}
              placeholder="e.g. 2026"
              className="bg-background border border-border/80 rounded-xl px-3 py-2 text-sm text-foreground w-28 focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {/* Language */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Language</label>
            <select
              value={filters.language || ""}
              onChange={(e) => setFilters((f) => ({ ...f, language: e.target.value || undefined }))}
              className="bg-background border border-border/80 rounded-xl px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">All Languages</option>
              <option value="en">English</option>
              <option value="ur">Urdu (اردو)</option>
              <option value="ro">Roman Urdu</option>
            </select>
          </div>

          {activeFilterCount > 0 && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-destructive transition-colors px-2 py-2"
            >
              <X className="h-3.5 w-3.5" />
              Reset Filters
            </button>
          )}
        </div>
      )}

      {/* Results Container */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {loading && (
          <div className="flex items-center justify-center py-16 gap-3 text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="text-sm font-medium">Scanning Pakistani legal database...</span>
          </div>
        )}

        {!loading && query && results.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-muted-foreground text-center">
            <BookOpen className="h-10 w-10 opacity-30 text-primary" />
            <p className="text-sm font-semibold text-foreground">No statutory matches found for &ldquo;{query}&rdquo;</p>
            <p className="text-xs">Try searching by Section number (e.g. &ldquo;Section 302&rdquo;) or Article title.</p>
          </div>
        )}

        {!loading && !query && (
          <div className="flex flex-col items-center justify-center py-12 gap-5 text-center">
            <div className="h-14 w-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shadow-sm">
              <Search className="h-7 w-7" />
            </div>
            <div className="space-y-1">
              <h3 className="font-bold text-base text-foreground">Advanced Statutory & Case Law Search</h3>
              <p className="text-xs text-muted-foreground max-w-md">
                Search verified Pakistani legal codes by keyword, section, or act year across full vector indices.
              </p>
            </div>

            {/* Popular Searches */}
            <div className="w-full max-w-xl space-y-2 pt-2">
              <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider flex items-center justify-center gap-1">
                <Tag className="h-3 w-3" /> Popular Legal Topics:
              </span>
              <div className="flex flex-wrap gap-2 justify-center">
                {POPULAR_SEARCHES.map((item) => (
                  <button
                    key={item}
                    onClick={() => { setQuery(item); setPage(1); }}
                    className="text-xs bg-card hover:bg-muted border border-border/80 px-3 py-1.5 rounded-full text-foreground transition-all hover:border-primary/40 shadow-2xs"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {!loading && results.length > 0 && (
          <>
            <div className="flex items-center justify-between px-1">
              <p className="text-xs text-muted-foreground font-medium">
                Found <span className="font-bold text-foreground">{total.toLocaleString()}</span> legal occurrences for &ldquo;{query}&rdquo;
              </p>
            </div>

            {results.map((r, idx) => (
              <SearchResultCard key={`${r.document_id}-${idx}`} result={r} query={query} />
            ))}

            {/* Pagination Controls */}
            {total > 10 && (
              <div className="flex justify-center items-center gap-3 pt-6 pb-2">
                <button
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="px-4 py-2 rounded-xl text-xs font-semibold border border-border/80 bg-card hover:bg-muted disabled:opacity-40 transition-all"
                >
                  Previous
                </button>
                <span className="text-xs font-medium text-muted-foreground">
                  Page <b className="text-foreground">{page}</b> of {Math.ceil(total / 10)}
                </span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= Math.ceil(total / 10)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold border border-border/80 bg-card hover:bg-muted disabled:opacity-40 transition-all"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function SearchResultCard({ result: r, query }: { result: SearchResult; query: string }) {
  const [copied, setCopied] = useState(false);

  const highlight = (text: string) => {
    if (!query) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="bg-emerald-500/20 text-emerald-800 dark:text-emerald-200 font-semibold rounded px-1">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  const copySnippet = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    navigator.clipboard.writeText(`${r.document_title}${r.section_number ? ` (Section ${r.section_number})` : ''}: "${r.content}"`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-card border border-border/80 rounded-2xl p-5 hover:border-primary/40 hover:shadow-md transition-all space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-sm text-foreground group-hover:text-primary transition-colors">
              {r.document_title}
            </span>
            {r.document_type && (
              <span className="text-[10px] font-bold bg-primary/10 text-primary px-2 py-0.5 rounded-md uppercase tracking-wider">
                {r.document_type}
              </span>
            )}
          </div>

          {r.section_number && (
            <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              Section {r.section_number} {r.section_title ? `— ${r.section_title}` : ''}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span
            className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${
              r.score >= 0.8
                ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                : r.score >= 0.5
                ? "bg-amber-500/10 text-amber-600 border-amber-500/20"
                : "bg-muted text-muted-foreground border-border"
            }`}
          >
            {Math.round(r.score * 100)}% Match
          </span>
          <button
            onClick={copySnippet}
            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-all"
            title="Copy Legal Excerpt"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      <p className="text-xs text-muted-foreground leading-relaxed bg-muted/30 p-3 rounded-xl border border-border/40">
        {highlight(truncate(r.content, 260))}
      </p>

      <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
        {r.page_number ? <span>Page Reference: {r.page_number}</span> : <span />}
        <a 
          href={`/documents/${r.document_id}`} 
          className="text-primary hover:underline font-semibold flex items-center gap-1"
        >
          View Full Act <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </div>
  );
}

