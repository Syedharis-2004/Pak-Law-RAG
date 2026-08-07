"use client";

import React, { useCallback, useRef, useState } from "react";
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { formatFileSize } from "@/lib/utils";

interface UploadFile {
  id: string;
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  progress: number;
  error?: string;
}

interface DocumentUploaderProps {
  onUploadComplete?: (documentId: string, filename: string) => void;
}

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/msword",
  "text/plain",
];
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB

export default function DocumentUploader({ onUploadComplete }: DocumentUploaderProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFiles = useCallback((rawFiles: FileList | File[]) => {
    const fileArray = Array.from(rawFiles);
    const newEntries: UploadFile[] = fileArray
      .filter((f) => ACCEPTED_TYPES.includes(f.type) && f.size <= MAX_FILE_SIZE)
      .map((f) => ({
        id: `${Date.now()}-${Math.random()}`,
        file: f,
        status: "pending",
        progress: 0,
      }));

    setFiles((prev) => [...prev, ...newEntries]);

    // Start uploading each new file
    newEntries.forEach((entry) => uploadFile(entry));
  }, []);

  const uploadFile = async (entry: UploadFile) => {
    const token = localStorage.getItem("paklaw_token");

    setFiles((prev) =>
      prev.map((f) => (f.id === entry.id ? { ...f, status: "uploading" } : f))
    );

    try {
      const formData = new FormData();
      formData.append("file", entry.file);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${process.env.NEXT_PUBLIC_API_URL || "https://pak-law-rag.onrender.com"}/api/v1/documents/upload`);
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          setFiles((prev) =>
            prev.map((f) => (f.id === entry.id ? { ...f, progress: pct } : f))
          );
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const res = JSON.parse(xhr.responseText);
          setFiles((prev) =>
            prev.map((f) =>
              f.id === entry.id ? { ...f, status: "done", progress: 100 } : f
            )
          );
          onUploadComplete?.(res.id, entry.file.name);
        } else {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === entry.id
                ? { ...f, status: "error", error: "Upload failed" }
                : f
            )
          );
        }
      };

      xhr.onerror = () => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === entry.id
              ? { ...f, status: "error", error: "Network error" }
              : f
          )
        );
      };

      xhr.send(formData);
    } catch (err) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === entry.id ? { ...f, status: "error", error: "Unknown error" } : f
        )
      );
    }
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  };

  const statusIcon = (status: UploadFile["status"]) => {
    switch (status) {
      case "uploading":
        return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
      case "done":
        return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-destructive" />;
      default:
        return <FileText className="h-4 w-4 text-muted-foreground" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all
          ${isDragging
            ? "border-primary bg-primary/5 scale-[1.01]"
            : "border-border bg-muted/40 hover:bg-muted/60 hover:border-primary/50"
          }`}
      >
        <div className={`p-4 rounded-full transition-all ${isDragging ? "bg-primary/10" : "bg-background"}`}>
          <Upload className={`h-8 w-8 transition-colors ${isDragging ? "text-primary" : "text-muted-foreground"}`} />
        </div>
        <div className="text-center">
          <p className="text-sm font-semibold text-foreground">
            {isDragging ? "Release to upload" : "Drag & drop documents here"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            PDF, DOCX, DOC, TXT — max 50 MB each
          </p>
        </div>
        <span className="px-4 py-1.5 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 transition-colors">
          Browse Files
        </span>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.doc,.txt"
          className="hidden"
          onChange={(e) => e.target.files && processFiles(e.target.files)}
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((f) => (
            <li
              key={f.id}
              className="flex items-center gap-3 bg-card border border-border rounded-lg px-4 py-3 group"
            >
              {statusIcon(f.status)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{f.file.name}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-muted-foreground">{formatFileSize(f.file.size)}</span>
                  {f.status === "uploading" && (
                    <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all duration-300"
                        style={{ width: `${f.progress}%` }}
                      />
                    </div>
                  )}
                  {f.status === "error" && (
                    <span className="text-xs text-destructive">{f.error}</span>
                  )}
                  {f.status === "done" && (
                    <span className="text-xs text-emerald-500">Indexed successfully</span>
                  )}
                </div>
              </div>
              {(f.status === "done" || f.status === "error" || f.status === "pending") && (
                <button
                  onClick={() => removeFile(f.id)}
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
