"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/sidebar";
import { api } from "@/lib/api";
import { 
  Upload, 
  FileText, 
  Trash2, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  ExternalLink,
  Loader2,
  Database,
  Sparkles
} from "lucide-react";

interface DocumentItem {
  id: string;
  title: string;
  document_type: string;
  file_name: string;
  file_size_bytes: number;
  status: string;
  total_chunks: number;
  created_at: string;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [docType, setDocType] = useState("act");
  
  // Drag state
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const res = await api.get<{ items: DocumentItem[] }>("/api/v1/documents");
      setDocuments(res.items);
    } catch (e) {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", docType);

    try {
      await api.post("/api/v1/documents/upload", formData);
      loadDocuments();
    } catch (e: any) {
      alert(e.message || "File upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this legal document? Vector indices will be pruned.")) return;

    try {
      await api.delete(`/api/v1/documents/${id}`);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (e) {
      alert("Failed to delete document");
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
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
              <Database className="h-4 w-4" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-foreground leading-none">Document Library & Vector Ingestion</h2>
              <span className="text-[10px] text-muted-foreground">Manage Acts, Ordinances, Contracts, and Court Judgments</span>
            </div>
          </div>

          <button
            onClick={loadDocuments}
            className="flex items-center gap-1.5 p-2 bg-card hover:bg-muted border border-border/60 rounded-xl text-xs font-semibold text-muted-foreground hover:text-foreground transition-all shadow-2xs"
            title="Refresh List"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-primary" : ""}`} />
            <span>Sync Index</span>
          </button>
        </header>

        {/* Layout Split */}
        <div className="flex-1 flex overflow-hidden p-6 gap-6">
          
          {/* Left Uploader Card */}
          <div className="w-80 sm:w-96 flex flex-col gap-4 shrink-0">
            <div className="p-6 bg-card border border-border/80 rounded-2xl space-y-4 shadow-sm">
              <div className="space-y-1">
                <h3 className="font-bold text-sm text-foreground flex items-center gap-2">
                  <Upload className="h-4 w-4 text-primary" /> Upload Legal Document
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Supported formats: PDF, DOCX, TXT, HTML, MD. Scanned PDFs parsed with automatic OCR pipeline.
                </p>
              </div>

              {/* Ingestion Classifier */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider" htmlFor="classification">
                  Statute Classification
                </label>
                <select
                  id="classification"
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="w-full bg-background border border-border/80 rounded-xl px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 font-medium"
                >
                  <option value="act">Act of Parliament</option>
                  <option value="ordinance">Presidential Ordinance</option>
                  <option value="rules">Statutory Rules & Regulations</option>
                  <option value="judgment">High Court / Supreme Court Judgment</option>
                  <option value="contract">Commercial Agreement / Contract</option>
                </select>
              </div>

              {/* Drag & Drop Area */}
              <div
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
                  dragActive 
                    ? "border-primary bg-primary/10 scale-[0.99]" 
                    : "border-border/80 hover:border-primary/50 bg-muted/20"
                }`}
                onClick={() => document.getElementById("file-input")?.click()}
              >
                <input
                  id="file-input"
                  type="file"
                  className="hidden"
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.txt,.html,.md"
                />
                
                {uploading ? (
                  <div className="space-y-3 flex flex-col items-center">
                    <Loader2 className="h-8 w-8 text-primary animate-spin" />
                    <div className="space-y-0.5">
                      <p className="text-xs font-bold text-foreground">Vectorizing document...</p>
                      <p className="text-[10px] text-muted-foreground">Chunking sections & building Qdrant points</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2.5 flex flex-col items-center">
                    <div className="h-12 w-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                      <Upload className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-foreground">Drag & drop or Click to Browse</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">Up to 50MB file size limit</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Document Ingestion Table */}
          <div className="flex-1 bg-card border border-border/80 rounded-2xl shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 border-b border-border/60 bg-muted/20 flex items-center justify-between">
              <h3 className="font-bold text-sm text-foreground flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" /> Indexed Workspace Corpus
              </h3>
              <span className="text-xs text-muted-foreground font-semibold bg-background px-2.5 py-1 rounded-lg border border-border/50">
                {documents.length} Total Files
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              {documents.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center py-20 text-muted-foreground text-center space-y-3">
                  <FileText className="h-12 w-12 opacity-25 text-primary" />
                  <div>
                    <p className="text-sm font-semibold text-foreground">No legal documents indexed yet</p>
                    <p className="text-xs text-muted-foreground mt-0.5">Upload acts or court rulings to start querying them with AI</p>
                  </div>
                </div>
              ) : (
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-border/60 text-[11px] font-bold text-muted-foreground uppercase tracking-wider bg-muted/10">
                      <th className="p-4">Document Title</th>
                      <th className="p-4">Classification</th>
                      <th className="p-4">Size</th>
                      <th className="p-4">Vector Status</th>
                      <th className="p-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60 text-xs font-medium">
                    {documents.map((doc) => (
                      <tr key={doc.id} className="hover:bg-muted/30 transition-colors">
                        <td className="p-4 max-w-xs truncate">
                          <span className="font-bold text-foreground block truncate">{doc.title}</span>
                          <span className="text-[11px] text-muted-foreground font-normal truncate block">{doc.file_name}</span>
                        </td>
                        <td className="p-4">
                          <span className="bg-primary/10 text-primary px-2.5 py-1 rounded-md font-bold uppercase text-[10px] tracking-wider">
                            {doc.document_type}
                          </span>
                        </td>
                        <td className="p-4 text-muted-foreground">{formatBytes(doc.file_size_bytes)}</td>
                        <td className="p-4">
                          {doc.status === "ready" && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 font-semibold border border-emerald-500/20">
                              <CheckCircle2 className="h-3.5 w-3.5" /> Ready ({doc.total_chunks} Chunks)
                            </span>
                          )}
                          {doc.status === "processing" && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] text-amber-600 bg-amber-500/10 font-semibold border border-amber-500/20">
                              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Ingesting OCR...
                            </span>
                          )}
                          {doc.status === "failed" && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] text-destructive bg-destructive/10 font-semibold border border-destructive/20">
                              <AlertCircle className="h-3.5 w-3.5" /> Extraction Failed
                            </span>
                          )}
                          {doc.status === "pending" && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] text-muted-foreground bg-muted font-semibold border border-border">
                              <Clock className="h-3.5 w-3.5" /> In Queue
                            </span>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="p-2 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded-xl transition-colors"
                            title="Delete Document"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

