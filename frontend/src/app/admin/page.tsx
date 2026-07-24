"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/sidebar";
import { api } from "@/lib/api";
import { 
  Users, 
  FileText, 
  MessageSquare, 
  HardDrive, 
  Loader2,
  ShieldCheck,
  ArrowUpRight,
  TrendingUp,
  Activity
} from "lucide-react";

interface Stats {
  total_users: number;
  total_documents: number;
  total_ai_messages: number;
  total_storage_used_mb: number;
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    setLoading(true);
    try {
      const res = await api.get<{ stats: Stats }>("/api/v1/admin/analytics/summary");
      setStats(res.stats);
    } catch (e) {
      // Ignore unauthorized redirects
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <Sidebar />

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-border/60 bg-card/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-foreground leading-none">System Administration & Analytics</h2>
              <span className="text-[10px] text-muted-foreground">Platform Telemetry & Ingestion Metrics</span>
            </div>
          </div>

          <span className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold text-[10px] px-3 py-1 rounded-full uppercase tracking-wider flex items-center gap-1 border border-emerald-500/20">
            <ShieldCheck className="h-3.5 w-3.5" /> Secure Counsel Mode
          </span>
        </header>

        {/* Workspace Container */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="h-full flex items-center justify-center py-20 gap-3 text-muted-foreground">
              <Loader2 className="h-6 w-6 text-primary animate-spin" />
              <span className="text-sm font-semibold">Gathering administrator metrics...</span>
            </div>
          ) : stats ? (
            <>
              {/* Stat Cards Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                
                {/* Total Users */}
                <div className="bg-card border border-border/80 p-6 rounded-2xl shadow-sm relative overflow-hidden group hover:border-primary/40 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Active Users</span>
                    <div className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                      <Users className="h-4 w-4" />
                    </div>
                  </div>
                  <p className="text-3xl font-extrabold text-foreground mt-3 tracking-tight">{stats.total_users}</p>
                  <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1 mt-2">
                    <ArrowUpRight className="h-3.5 w-3.5" /> Verified legal practitioners
                  </p>
                </div>

                {/* Total Statutes */}
                <div className="bg-card border border-border/80 p-6 rounded-2xl shadow-sm relative overflow-hidden group hover:border-primary/40 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Indexed Statutes</span>
                    <div className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                      <FileText className="h-4 w-4" />
                    </div>
                  </div>
                  <p className="text-3xl font-extrabold text-foreground mt-3 tracking-tight">{stats.total_documents}</p>
                  <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1 mt-2">
                    <ArrowUpRight className="h-3.5 w-3.5" /> Acts, regulations & precedents
                  </p>
                </div>

                {/* Total AI Messages */}
                <div className="bg-card border border-border/80 p-6 rounded-2xl shadow-sm relative overflow-hidden group hover:border-primary/40 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">RAG Evaluated</span>
                    <div className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                      <MessageSquare className="h-4 w-4" />
                    </div>
                  </div>
                  <p className="text-3xl font-extrabold text-foreground mt-3 tracking-tight">{stats.total_ai_messages}</p>
                  <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1 mt-2">
                    <ArrowUpRight className="h-3.5 w-3.5" /> Multilingual queries answered
                  </p>
                </div>

                {/* Storage Used */}
                <div className="bg-card border border-border/80 p-6 rounded-2xl shadow-sm relative overflow-hidden group hover:border-primary/40 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Vector Storage</span>
                    <div className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                      <HardDrive className="h-4 w-4" />
                    </div>
                  </div>
                  <p className="text-3xl font-extrabold text-foreground mt-3 tracking-tight">
                    {stats.total_storage_used_mb} <span className="text-sm font-normal text-muted-foreground">MB</span>
                  </p>
                  <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1 mt-2">
                    <ArrowUpRight className="h-3.5 w-3.5" /> Dense embeddings & OCR assets
                  </p>
                </div>

              </div>

              {/* Graphical Charts Section */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* SVG Telemetry Chart card */}
                <div className="bg-card border border-border/80 rounded-2xl shadow-sm p-6 lg:col-span-2 space-y-4">
                  <div className="flex items-center justify-between border-b border-border/60 pb-3">
                    <h3 className="font-bold text-sm text-foreground flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-primary" />
                      Weekly Legal Search & Inference Frequency
                    </h3>
                  </div>

                  {/* SVG Bar Chart */}
                  <div className="h-64 flex items-end justify-between gap-4 pt-8 px-2">
                    {[
                      { day: "Mon", count: 180 },
                      { day: "Tue", count: 340 },
                      { day: "Wed", count: 520 },
                      { day: "Thu", count: 410 },
                      { day: "Fri", count: 680 },
                      { day: "Sat", count: 290 },
                      { day: "Sun", count: 140 },
                    ].map((item, idx) => {
                      const maxVal = 700;
                      const heightPercent = (item.count / maxVal) * 100;
                      return (
                        <div key={idx} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                          <span className="text-[10px] font-bold text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-150 bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                            {item.count}
                          </span>
                          <div 
                            style={{ height: `${heightPercent}%` }} 
                            className="w-full bg-primary/20 group-hover:bg-primary rounded-t-xl transition-all duration-200 shadow-xs"
                          />
                          <span className="text-xs text-muted-foreground font-bold">{item.day}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Storage breakdown card */}
                <div className="bg-card border border-border/80 rounded-2xl shadow-sm p-6 space-y-4">
                  <h3 className="font-bold text-sm text-foreground">Ingested Corpus Breakdown</h3>
                  <div className="space-y-4 pt-2">
                    {[
                      { type: "Acts of Parliament", pct: 60, color: "bg-primary" },
                      { type: "High Court Judgments", pct: 25, color: "bg-emerald-500" },
                      { type: "Commercial Contracts", pct: 15, color: "bg-teal-400" },
                    ].map((item, idx) => (
                      <div key={idx} className="space-y-1.5">
                        <div className="flex justify-between text-xs font-semibold">
                          <span className="text-foreground">{item.type}</span>
                          <span className="text-muted-foreground">{item.pct}%</span>
                        </div>
                        <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                          <div className={`h-full ${item.color} rounded-full transition-all duration-500`} style={{ width: `${item.pct}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center text-muted-foreground py-20">
              <ShieldCheck className="h-10 w-10 opacity-20 mb-2 text-primary" />
              <h4 className="font-bold text-foreground">Access Restricted</h4>
              <p className="text-xs">Administrator authorization required to view platform stats.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

