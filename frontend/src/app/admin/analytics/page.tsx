"use client";

import React from "react";
import Sidebar from "@/components/sidebar";
import { BarChart2, TrendingUp, Users, Activity, Clock } from "lucide-react";
import AdminDashboard from "@/components/admin-dashboard";

export default function AnalyticsAdminPage() {
  // Mock data to feed into the AdminDashboard component we already built
  const mockAnalytics = {
    total_queries: 12450,
    total_documents: 450,
    total_users: 128,
    avg_response_time_ms: 1250,
    queries_today: 342,
    documents_pending: 2,
    documents_failed: 1,
    uptime_hours: 720,
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <header className="h-16 border-b border-border bg-card px-6 flex items-center gap-2 shrink-0">
          <BarChart2 className="h-5 w-5 text-primary" />
          <h2 className="font-semibold text-foreground">System Analytics</h2>
        </header>

        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {/* Reuse the dashboard cards */}
          <AdminDashboard analytics={mockAnalytics} loading={false} />

          {/* Additional Mock Charts Area */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm h-80 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" /> Daily Queries
                </h3>
                <span className="text-xs text-muted-foreground">Last 7 Days</span>
              </div>
              <div className="flex-1 flex items-end gap-2 pt-4">
                {/* Mock bar chart bars */}
                {[40, 60, 45, 80, 55, 90, 75].map((h, i) => (
                  <div key={i} className="flex-1 flex flex-col justify-end items-center gap-2 h-full">
                    <div 
                      className="w-full bg-primary/20 hover:bg-primary/40 rounded-t-sm transition-all"
                      style={{ height: `${h}%` }}
                    />
                    <span className="text-[10px] text-muted-foreground">D-{6-i}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-card border border-border rounded-xl p-5 shadow-sm h-80 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4 text-amber-500" /> Response Time (ms)
                </h3>
                <span className="text-xs text-muted-foreground">Avg Latency</span>
              </div>
              <div className="flex-1 flex flex-col justify-center items-center gap-2 opacity-50">
                <Activity className="h-12 w-12 text-muted-foreground" />
                <p className="text-sm">Detailed latency metrics graph will appear here.</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
