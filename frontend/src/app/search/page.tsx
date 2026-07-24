"use client";

import React, { useState } from "react";
import Sidebar from "@/components/sidebar";
import { api } from "@/lib/api";
import { Search, Filter, Clock, FileText, Globe } from "lucide-react";

interface SearchResultItem {
  document_id: string;
  chunk_id: string;
  document_title: string;
  document_type: string;
  jurisdiction?: string;
  year?: number;
  section_number?: string;
  section_title?: string;
  content: string;
  page_number?: number;
  score: number;
  search_type: string;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [searchType, setSearchType] = useState("hybrid");
  
  // Filters
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedJurisdictions, setSelectedJurisdictions] = useState<string[]>([]);
  const [yearFilter, setYearFilter] = useState("");

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [total, setTotal] = useState(0);
  const [searchTime, setSearchTime] = useState<number | null>(null);
  const [langDetected, setLangDetected] = useState<string | null>(null);

  const documentTypes = ["act", "ordinance", "rules", "judgment", "contract"];
  const jurisdictions = ["Federal", "Punjab", "Sindh", "KPK", "Balochistan"];

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResults([]);

    try {
      const res = await api.post<{
        results: SearchResultItem[];
        total: number;
        search_time_ms: number;
        language_detected: string;
      }>("/api/v1/search", {
        query,
        search_type: searchType,
        document_types: selectedTypes.length > 0 ? selectedTypes : undefined,
        jurisdictions: selectedJurisdictions.length > 0 ? selectedJurisdictions : undefined,
        years: yearFilter ? [parseInt(yearFilter)] : undefined,
        top_k: 20,
      });

      setResults(res.results);
      setTotal(res.total);
      setSearchTime(res.search_time_ms);
      setLangDetected(res.language_detected);
    } catch (e) {
      // Error handling logic
    } finally {
      setLoading(false);
    }
  };

  const toggleTypeFilter = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const toggleJurisdictionFilter = (jur: string) => {
    setSelectedJurisdictions((prev) =>
      prev.includes(jur) ? prev.filter((j) => j !== jur) : [...prev, jur]
    );
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar />

      {/* Main Container */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-border bg-card px-6 flex items-center">
          <h2 className="font-semibold text-foreground text-lg">Advanced Hybrid Search Workspace</h2>
        </header>

        {/* Content splits into filters and workspace */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left: Filters Panel */}
          <aside className="w-64 border-r border-border bg-card p-6 flex flex-col gap-6 overflow-y-auto">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <Filter className="h-4 w-4 text-primary" />
              <h3 className="font-semibold text-sm">Filters & Facets</h3>
            </div>

            {/* Search Type */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Search Strategy</h4>
              <select
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none"
              >
                <option value="hybrid">Dense + Sparse Hybrid</option>
                <option value="semantic">Dense Semantic Only</option>
                <option value="keyword">BM25 Keyword Only</option>
              </select>
            </div>

            {/* Document Types */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Document Category</h4>
              <div className="space-y-1">
                {documentTypes.map((type) => (
                  <label key={type} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedTypes.includes(type)}
                      onChange={() => toggleTypeFilter(type)}
                      className="rounded border-border text-primary focus:ring-primary/20"
                    />
                    <span className="capitalize">{type}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Jurisdictions */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Jurisdiction</h4>
              <div className="space-y-1">
                {jurisdictions.map((jur) => (
                  <label key={jur} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedJurisdictions.includes(jur)}
                      onChange={() => toggleJurisdictionFilter(jur)}
                      className="rounded border-border text-primary focus:ring-primary/20"
                    />
                    <span>{jur}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Year Input */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Year of Enactment</h4>
              <input
                type="number"
                placeholder="e.g. 1973"
                value={yearFilter}
                onChange={(e) => setYearFilter(e.target.value)}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none"
              />
            </div>
          </aside>

          {/* Right: Workspace & Results */}
          <div className="flex-1 flex flex-col overflow-hidden bg-muted/20">
            {/* Search Input Bar */}
            <div className="p-6 bg-card border-b border-border">
              <form onSubmit={handleSearch} className="flex gap-2 max-w-3xl">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground/60" />
                  <input
                    type="text"
                    required
                    placeholder="Search section number, keywords, act titles..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-background text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-primary text-primary-foreground px-6 rounded-xl hover:bg-primary/95 font-medium transition-all"
                >
                  {loading ? "Searching..." : "Search"}
                </button>
              </form>

              {/* Stats Bar */}
              {searchTime !== null && (
                <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground px-1">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    Query processed in {searchTime.toFixed(1)}ms
                  </span>
                  <span className="flex items-center gap-1">
                    <Globe className="h-3.5 w-3.5" />
                    Query Language: <b className="uppercase">{langDetected}</b>
                  </span>
                  <span>Total Hits: {total}</span>
                </div>
              )}
            </div>

            {/* Results Scroll Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 max-w-4xl">
              {results.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground py-20 text-center">
                  <Search className="h-10 w-10 opacity-20 mb-2" />
                  <p className="text-sm">Enter search parameters above to retrieve legal provisions</p>
                </div>
              ) : (
                results.map((item, idx) => (
                  <div key={idx} className="p-5 bg-card border border-border rounded-xl shadow-sm space-y-3 hover:shadow-md transition-all">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="bg-primary/10 text-primary px-2 py-0.5 rounded font-bold uppercase text-[10px]">{item.document_type}</span>
                        <span className="font-semibold text-foreground">{item.document_title}</span>
                      </div>
                      <span className="text-muted-foreground font-semibold">Match Score: {Math.round(item.score * 100)}%</span>
                    </div>

                    {item.section_number && (
                      <p className="text-sm font-bold text-foreground">Section {item.section_number} - {item.section_title || "Untitled"}</p>
                    )}

                    <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">{item.content}</p>

                    {item.page_number && (
                      <div className="flex items-center gap-1 text-[10px] text-muted-foreground pt-1 border-t border-border/50">
                        <FileText className="h-3 w-3" />
                        <span>Page {item.page_number}</span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
