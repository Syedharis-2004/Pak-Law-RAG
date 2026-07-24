"use client";

import React from "react";
import Link from "next/link";
import { 
  Scale, 
  ArrowRight, 
  ShieldCheck, 
  Zap, 
  Globe, 
  Sparkles, 
  CheckCircle2, 
  Search, 
  FileText,
  BookOpen
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-between relative overflow-hidden bg-radial-gradient">
      {/* Navbar */}
      <header className="h-16 border-b border-border/60 bg-card/80 backdrop-blur-md px-6 md:px-12 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-xs">
            <Scale className="h-5 w-5" />
          </div>
          <span className="font-bold text-lg tracking-tight text-foreground">PakLaw AI</span>
        </div>
        <div className="flex items-center gap-4">
          <Link 
            href="/auth/login" 
            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-lg hover:bg-muted/50"
          >
            Sign In
          </Link>
          <Link 
            href="/auth/register" 
            className="bg-primary text-primary-foreground px-4 py-2 rounded-xl text-sm font-medium hover:bg-primary/90 transition-all shadow-md shadow-primary/15 hover:-translate-y-0.5 active:translate-y-0"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-6xl mx-auto px-6 md:px-12 py-16 flex flex-col items-center justify-center text-center space-y-10">
        
        {/* Category Pill */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 shadow-xs">
          <Sparkles className="h-3.5 w-3.5" /> Next-Generation Pakistani Legal Workspace
        </div>

        {/* Title */}
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-[1.15] max-w-4xl">
          The Intelligent AI Legal Copilot for <span className="gradient-text">Pakistani Law</span>
        </h1>

        {/* Description */}
        <p className="text-base md:text-lg text-muted-foreground max-w-2xl leading-relaxed">
          Query statutory codes, analyze contracts, track amendments, and draft formal legal notices instantly. Grounded strictly in the Constitution, PPC, CrPC, CPC, and High Court judgments.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 pt-2">
          <Link
            href="/auth/register"
            className="w-full sm:w-auto bg-primary text-primary-foreground px-8 py-3.5 rounded-xl font-semibold hover:bg-primary/95 transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20 hover:-translate-y-0.5"
          >
            Start Legal Research
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/auth/login"
            className="w-full sm:w-auto bg-card border border-border/80 px-8 py-3.5 rounded-xl font-semibold hover:bg-muted/80 transition-all text-foreground"
          >
            Sign In to Workspace
          </Link>
        </div>

        {/* Interactive Mock Legal Query Preview Card */}
        <div className="w-full max-w-3xl glass-panel rounded-2xl p-6 border border-border/80 shadow-2xl text-left space-y-4 relative mt-6">
          <div className="flex items-center justify-between border-b border-border/50 pb-3">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-red-400/80" />
              <div className="h-3 w-3 rounded-full bg-amber-400/80" />
              <div className="h-3 w-3 rounded-full bg-emerald-400/80" />
            </div>
            <span className="text-[11px] font-mono text-muted-foreground uppercase tracking-widest">
              LangGraph RAG Engine • Hybrid Qdrant Vector Scan
            </span>
          </div>

          <div className="space-y-3">
            <div className="flex items-start gap-3 bg-muted/40 p-3.5 rounded-xl border border-border/40">
              <Search className="h-4 w-4 text-primary mt-0.5 shrink-0" />
              <p className="text-xs font-medium text-foreground">
                <span className="text-muted-foreground font-normal">Query:</span> &quot;What are the statutory grounds for temporary injunction under Order 39 Rules 1 & 2 CPC 1908?&quot;
              </p>
            </div>

            <div className="bg-card p-4 rounded-xl border border-border/60 shadow-xs space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4" /> Verified Answer (Confidence: 98.4%)
                </span>
                <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-bold uppercase">
                  CPC 1908
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Under Order XXXIX Rules 1 & 2 of the Code of Civil Procedure 1908, the court evaluates three cardinal principles: (1) Prima facie case, (2) Balance of convenience, and (3) Irreparable loss or injury.
              </p>
              <div className="flex gap-2 pt-1">
                <span className="text-[10px] bg-muted px-2 py-1 rounded-md text-foreground font-mono">
                  [1] CPC 1908, Order XXXIX, Rule 1
                </span>
                <span className="text-[10px] bg-muted px-2 py-1 rounded-md text-foreground font-mono">
                  [2] 2023 SCMR 1421 (Supreme Court)
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full pt-10 text-left">
          
          {/* Card 1 */}
          <div className="p-6 bg-card/80 border border-border/80 rounded-2xl space-y-3 hover:border-primary/40 hover:shadow-md transition-all">
            <div className="h-10 w-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary border border-primary/20">
              <Zap className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-foreground text-base">LangGraph RAG Workflow</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Multi-step query analysis fusing dense vector embeddings with BM25 lexical search for exact statutory recall.
            </p>
          </div>

          {/* Card 2 */}
          <div className="p-6 bg-card/80 border border-border/80 rounded-2xl space-y-3 hover:border-primary/40 hover:shadow-md transition-all">
            <div className="h-10 w-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary border border-primary/20">
              <Globe className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-foreground text-base">Trilingual Support</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Ask queries and draft formal legal notices seamlessly in English, Urdu (اردو), or Roman Urdu.
            </p>
          </div>

          {/* Card 3 */}
          <div className="p-6 bg-card/80 border border-border/80 rounded-2xl space-y-3 hover:border-primary/40 hover:shadow-md transition-all">
            <div className="h-10 w-10 bg-primary/10 rounded-xl flex items-center justify-center text-primary border border-primary/20">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="font-bold text-foreground text-base">Zero Hallucination Guarantee</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Strict legal grounding citing section numbers, ordinance titles, and precise page occurrences.
            </p>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="h-16 border-t border-border/60 bg-card/80 px-6 md:px-12 flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <Scale className="h-4 w-4 text-primary" />
          <span>© {new Date().getFullYear()} PakLaw AI • Enterprise Legal Workspace.</span>
        </div>
        <div className="flex gap-4">
          <a href="#" className="hover:text-foreground transition-colors">Terms of Service</a>
          <a href="#" className="hover:text-foreground transition-colors">Privacy Policy</a>
        </div>
      </footer>
    </div>
  );
}

