"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/sidebar";
import { FileText, Search, MoreVertical, RefreshCw, Trash2, Eye } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface DocumentMeta {
  id: string;
  title: string;
  type: string;
  status: "completed" | "processing" | "failed";
  chunks: number;
  created_at: string;
}

export default function DocumentsAdminPage() {
  const [documents, setDocuments] = useState<DocumentMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    // Mock data for UI
    setDocuments([
      { id: "doc_1", title: "Constitution of Pakistan 1973", type: "Constitution", status: "completed", chunks: 1450, created_at: "2023-12-01T10:00:00Z" },
      { id: "doc_2", title: "Pakistan Penal Code (PPC) 1860", type: "Act", status: "completed", chunks: 3200, created_at: "2023-12-05T14:30:00Z" },
      { id: "doc_3", title: "PLD 2024 SC 123 - Election Case", type: "Judgment", status: "completed", chunks: 120, created_at: "2024-04-10T09:15:00Z" },
      { id: "doc_4", title: "Companies Act 2017", type: "Act", status: "processing", chunks: 0, created_at: "2024-07-01T16:45:00Z" },
      { id: "doc_5", title: "Corrupted Scan File.pdf", type: "Unknown", status: "failed", chunks: 0, created_at: "2024-07-01T10:20:00Z" },
    ]);
    setLoading(false);
  }, []);

  const filteredDocs = documents.filter(d => 
    d.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <header className="h-16 border-b border-border bg-card px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <h2 className="font-semibold text-foreground">Corpus Management</h2>
          </div>
          <button className="flex items-center gap-2 bg-muted text-foreground border border-border px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-muted/80 transition-all">
            <RefreshCw className="h-4 w-4" />
            Sync Indexes
          </button>
        </header>

        <div className="flex-1 p-6 overflow-y-auto">
          <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 border-b border-border flex items-center justify-between gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search legal documents..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
                />
              </div>
              <div className="text-sm text-muted-foreground">
                Total: <span className="font-medium text-foreground">{documents.length}</span> items
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b border-border">
                  <tr>
                    <th className="px-6 py-3 font-medium">Document Title</th>
                    <th className="px-6 py-3 font-medium">Type</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                    <th className="px-6 py-3 font-medium">Vectors</th>
                    <th className="px-6 py-3 font-medium">Added</th>
                    <th className="px-6 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4 font-medium text-foreground max-w-xs truncate" title={doc.title}>
                        {doc.title}
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs bg-muted border border-border px-2 py-0.5 rounded-md text-muted-foreground">
                          {doc.type}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {doc.status === "completed" && <span className="text-emerald-500 text-xs font-medium">Indexed</span>}
                        {doc.status === "processing" && <span className="text-amber-500 text-xs font-medium flex items-center gap-1"><RefreshCw className="h-3 w-3 animate-spin"/> Processing</span>}
                        {doc.status === "failed" && <span className="text-red-500 text-xs font-medium">Failed</span>}
                      </td>
                      <td className="px-6 py-4 text-muted-foreground text-xs">
                        {doc.chunks.toLocaleString()} chunks
                      </td>
                      <td className="px-6 py-4 text-muted-foreground text-xs">
                        {formatDate(doc.created_at)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-1">
                          <button className="text-muted-foreground hover:text-primary transition-colors p-1.5 rounded-md hover:bg-primary/10" title="View">
                            <Eye className="h-4 w-4" />
                          </button>
                          <button className="text-muted-foreground hover:text-destructive transition-colors p-1.5 rounded-md hover:bg-destructive/10" title="Delete">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
