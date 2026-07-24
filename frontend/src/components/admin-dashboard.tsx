"use client";

import React from "react";
import {
  FileText,
  Clock,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  XCircle,
  BarChart2,
  ShieldCheck,
  Zap
} from "lucide-react";
import { formatDate } from "@/lib/utils";

interface SystemHealthMetric {
  label: string;
  value: string | number;
  status: "healthy" | "warning" | "critical" | "neutral";
  icon: React.ReactNode;
}

interface AnalyticsData {
  total_queries: number;
  total_documents: number;
  total_users: number;
  avg_response_time_ms: number;
  queries_today: number;
  documents_pending: number;
  documents_failed: number;
  uptime_hours: number;
}

interface AdminDashboardProps {
  analytics: AnalyticsData | null;
  loading?: boolean;
}

const statusColor: Record<string, string> = {
  healthy: "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  warning: "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20",
  critical: "text-red-600 dark:text-red-400 bg-red-500/10 border-red-500/20",
  neutral: "text-muted-foreground bg-muted border-border/50",
};

const statusIcon: Record<string, React.ReactNode> = {
  healthy: <CheckCircle2 className="h-3.5 w-3.5" />,
  warning: <AlertTriangle className="h-3.5 w-3.5" />,
  critical: <XCircle className="h-3.5 w-3.5" />,
  neutral: <BarChart2 className="h-3.5 w-3.5" />,
};

export default function AdminDashboard({ analytics, loading }: AdminDashboardProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 gap-3 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <span className="text-sm font-semibold">Aggregating system telemetry...</span>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3 text-muted-foreground">
        <AlertTriangle className="h-8 w-8 opacity-40 text-amber-500" />
        <p className="text-sm font-semibold">Analytics data unavailable</p>
      </div>
    );
  }

  const metrics: SystemHealthMetric[] = [
    {
      label: "Total Legal Queries",
      value: analytics.total_queries.toLocaleString(),
      status: "neutral",
      icon: <TrendingUp className="h-5 w-5 text-primary" />,
    },
    {
      label: "Queries Today",
      value: analytics.queries_today.toLocaleString(),
      status: analytics.queries_today > 0 ? "healthy" : "neutral",
      icon: <Clock className="h-5 w-5 text-primary" />,
    },
    {
      label: "Indexed Documents",
      value: analytics.total_documents.toLocaleString(),
      status: "healthy",
      icon: <FileText className="h-5 w-5 text-primary" />,
    },
    {
      label: "Avg Response Time",
      value: `${analytics.avg_response_time_ms} ms`,
      status: analytics.avg_response_time_ms < 3000 ? "healthy" : analytics.avg_response_time_ms < 6000 ? "warning" : "critical",
      icon: <Zap className="h-5 w-5 text-primary" />,
    },
    {
      label: "Pending Ingestion",
      value: analytics.documents_pending,
      status: analytics.documents_pending > 10 ? "warning" : "neutral",
      icon: <Loader2 className="h-5 w-5 text-primary" />,
    },
    {
      label: "Failed Documents",
      value: analytics.documents_failed,
      status: analytics.documents_failed > 0 ? "critical" : "healthy",
      icon: <XCircle className="h-5 w-5 text-primary" />,
    },
    {
      label: "Active Counsel Users",
      value: analytics.total_users.toLocaleString(),
      status: "healthy",
      icon: <ShieldCheck className="h-5 w-5 text-primary" />,
    },
    {
      label: "System Uptime",
      value: `${analytics.uptime_hours}h`,
      status: analytics.uptime_hours > 0 ? "healthy" : "critical",
      icon: <CheckCircle2 className="h-5 w-5 text-primary" />,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <MetricCard key={metric.label} metric={metric} />
      ))}
    </div>
  );
}

function MetricCard({ metric }: { metric: SystemHealthMetric }) {
  return (
    <div className="bg-card border border-border/80 rounded-2xl p-5 flex flex-col justify-between gap-4 hover:shadow-md transition-all duration-200 hover:border-primary/30 shadow-2xs">
      <div className="flex items-center justify-between">
        <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
          {metric.icon}
        </div>
        <span className={`flex items-center gap-1.5 text-[11px] font-bold ${statusColor[metric.status]} px-2.5 py-1 rounded-full border`}>
          {statusIcon[metric.status]}
          {metric.status.charAt(0).toUpperCase() + metric.status.slice(1)}
        </span>
      </div>
      <div>
        <p className="text-3xl font-extrabold text-foreground tracking-tight">{metric.value}</p>
        <p className="text-xs text-muted-foreground font-semibold mt-1">{metric.label}</p>
      </div>
    </div>
  );
}

