"use client";

import React, { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/sidebar";
import { api } from "@/lib/api";
import { 
  Send, 
  Loader2, 
  BookMarked, 
  ThumbsUp, 
  ThumbsDown, 
  Plus, 
  MessageSquare,
  HelpCircle,
  FileText,
  Bookmark,
  Scale,
  Sparkles,
  Copy,
  Check,
  X,
  History,
  Search,
  Globe
} from "lucide-react";

interface Citation {
  id: string;
  citation_number: number;
  document_title: string;
  section_number?: string;
  section_title?: string;
  page_number?: number;
  excerpt?: string;
  relevance_score?: number;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence_score?: number;
  suggested_questions?: string[];
  is_bookmarked?: boolean;
}

interface Conversation {
  id: string;
  title: string;
  mode: string;
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);
  
  // Scoped documents selection & Language
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [language, setLanguage] = useState("en");

  // Citation Panel state
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [isCitationOpen, setIsCitationOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const token = localStorage.getItem("paklaw_token");
    if (!token) {
      window.location.href = "/auth/login";
      return;
    }
    loadConversations();
  }, []);

  useEffect(() => {
    if (activeConversationId) {
      loadMessages(activeConversationId);
    } else {
      setMessages([]);
    }
  }, [activeConversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadConversations = async () => {
    try {
      const res = await api.get<{ items: Conversation[] }>("/api/v1/chat/conversations");
      setConversations(res.items);
      if (res.items.length > 0 && !activeConversationId) {
        setActiveConversationId(res.items[0].id);
      }
    } catch (e) {
      // Ignore initial load error
    }
  };

  const loadMessages = async (id: string) => {
    try {
      const res = await api.get<{ messages: Message[] }>(`/api/v1/chat/conversations/${id}`);
      setMessages(res.messages);
    } catch (e) {}
  };

  const handleStartNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setInput("");
  };

  const handleSendMessage = async (queryText: string) => {
    if (!queryText.trim() || loading) return;

    const userMsg: Message = {
      id: Math.random().toString(),
      role: "user",
      content: queryText,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    let assistantMsg: Message = {
      id: "streaming-temp",
      role: "assistant",
      content: "",
      citations: [],
      suggested_questions: [],
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      await api.stream(
        "/api/v1/chat/query",
        {
          message: queryText,
          conversation_id: activeConversationId || undefined,
          language: language,
          document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
          stream: true,
        },
        (chunk) => {
          if (chunk.type === "citations") {
            assistantMsg.citations = chunk.citations;
            setMessages((prev) =>
              prev.map((m) => (m.id === "streaming-temp" ? { ...assistantMsg } : m))
            );
          } else if (chunk.type === "token") {
            assistantMsg.content += chunk.content;
            setMessages((prev) =>
              prev.map((m) => (m.id === "streaming-temp" ? { ...assistantMsg } : m))
            );
          } else if (chunk.type === "metadata") {
            assistantMsg.confidence_score = chunk.confidence_score;
            assistantMsg.suggested_questions = chunk.suggested_questions;
            setMessages((prev) =>
              prev.map((m) => (m.id === "streaming-temp" ? { ...assistantMsg } : m))
            );
          } else if (chunk.type === "done") {
            assistantMsg.id = chunk.message_id;
            setMessages((prev) =>
              prev.map((m) => (m.id === "streaming-temp" ? { ...assistantMsg } : m))
            );
            setLoading(false);
            loadConversations();
          }
        }
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === "streaming-temp"
            ? { ...m, id: "error", content: "Sorry, an error occurred processing your legal query." }
            : m
        )
      );
      setLoading(false);
    }
  };

  const handleCopyText = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(id);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const handleBookmark = async (msgId: string) => {
    try {
      await api.post("/api/v1/chat/bookmarks", { message_id: msgId });
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, is_bookmarked: true } : m))
      );
    } catch (e) {}
  };

  const handleFeedback = async (msgId: string, rating: number) => {
    try {
      await api.post("/api/v1/chat/feedback", { message_id: msgId, rating });
    } catch (e) {}
  };

  const openCitationsPanel = (citations: Citation[]) => {
    setActiveCitations(citations);
    setIsCitationOpen(true);
  };

  const STARTER_PROMPTS = [
    { title: "Constitution Art 199", query: "What are the essential grounds and conditions for filing a Writ Petition under Article 199 of the Constitution of Pakistan?" },
    { title: "PPC Sec 302 vs 304", query: "Explain the legal distinctions and penal liabilities between Section 302 and Section 304 of Pakistan Penal Code (PPC)." },
    { title: "Bail Grounds CrPC 497", query: "What are the statutory requirements for granting pre-arrest and post-arrest bail under Section 497 CrPC?" },
    { title: "Contract Act Legal Notice", query: "Draft a formal legal notice for breach of commercial contract under the Contract Act 1872." },
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <Sidebar />

      {/* Main Workspace split */}
      <main className="flex-1 flex overflow-hidden relative">
        
        {/* Left History Panel */}
        <aside className="w-64 border-r border-border/80 bg-card/60 flex flex-col h-full hidden lg:flex">
          <div className="p-4 border-b border-border/60 flex items-center justify-between">
            <span className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
              <History className="h-3.5 w-3.5 text-primary" /> Past Consultations
            </span>
            <button
              onClick={handleStartNewConversation}
              className="p-1 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-all"
              title="New Thread"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-1">
            {conversations.length === 0 ? (
              <div className="text-center py-8 text-xs text-muted-foreground">
                No past consultations yet.
              </div>
            ) : (
              conversations.map((c) => {
                const isActive = c.id === activeConversationId;
                return (
                  <button
                    key={c.id}
                    onClick={() => setActiveConversationId(c.id)}
                    className={`w-full text-left px-3 py-2.5 rounded-xl text-xs font-medium transition-all flex items-center gap-2 truncate ${
                      isActive
                        ? "bg-primary/10 text-primary border border-primary/20 font-semibold"
                        : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                    }`}
                  >
                    <MessageSquare className="h-3.5 w-3.5 shrink-0" />
                    <span className="truncate">{c.title || "Legal Consultation"}</span>
                  </button>
                );
              })
            )}
          </div>
        </aside>

        {/* Center Chat Workspace */}
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
          {/* Header */}
          <header className="h-16 border-b border-border/60 bg-card/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                <Scale className="h-4 w-4" />
              </div>
              <div>
                <h2 className="font-bold text-sm text-foreground leading-none">PakLaw Legal Copilot</h2>
                <span className="text-[10px] text-muted-foreground">Grounded strictly in Pakistani Codes & Statutes</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Language picker */}
              <div className="flex items-center gap-1.5 bg-muted/60 px-3 py-1.5 rounded-xl border border-border/50 text-xs">
                <Globe className="h-3.5 w-3.5 text-muted-foreground" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-transparent text-xs text-foreground focus:outline-none font-medium cursor-pointer"
                >
                  <option value="en">English Legal</option>
                  <option value="ur">Urdu (اردو)</option>
                  <option value="ro">Roman Urdu</option>
                  <option value="hi">Hindi (हिंदी)</option>
                </select>
              </div>

              <button
                onClick={handleStartNewConversation}
                className="flex items-center gap-1.5 bg-primary text-primary-foreground px-3.5 py-1.5 rounded-xl text-xs font-semibold hover:bg-primary/90 transition-all shadow-xs"
              >
                <Plus className="h-3.5 w-3.5" />
                New Consultation
              </button>
            </div>
          </header>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto space-y-8 py-10">
                <div className="h-16 w-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shadow-md">
                  <Scale className="h-8 w-8" />
                </div>

                <div className="space-y-2">
                  <h3 className="text-2xl font-bold text-foreground">PakLaw Legal Workspace</h3>
                  <p className="text-sm text-muted-foreground max-w-md leading-relaxed">
                    Ask questions on Pakistani statutory acts, criminal procedure, civil procedure, or contract law. Verified by multi-step vector retrieval.
                  </p>
                </div>

                {/* Starter Question Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
                  {STARTER_PROMPTS.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(prompt.query)}
                      className="p-4 bg-card hover:bg-muted/60 border border-border/80 rounded-2xl transition-all duration-200 hover:border-primary/40 hover:-translate-y-0.5 space-y-1.5 shadow-xs"
                    >
                      <div className="flex items-center justify-between text-xs font-bold text-primary">
                        <span>{prompt.title}</span>
                        <Sparkles className="h-3 w-3 opacity-60" />
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                        {prompt.query}
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 max-w-3xl ${
                    msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`h-8 w-8 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 shadow-xs ${
                      msg.role === "user" 
                        ? "bg-primary text-primary-foreground" 
                        : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                    }`}
                  >
                    {msg.role === "user" ? "U" : <Scale className="h-4 w-4" />}
                  </div>

                  {/* Bubble Content */}
                  <div className="space-y-2 max-w-2xl">
                    <div
                      className={`rounded-2xl p-4 text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground shadow-sm font-medium"
                          : "bg-card border border-border/80 text-foreground shadow-sm"
                      }`}
                    >
                      {msg.content || (
                        <div className="flex items-center gap-2 text-muted-foreground text-xs">
                          <Loader2 className="h-4 w-4 animate-spin text-primary" />
                          <span>Searching Pakistan Law Database...</span>
                        </div>
                      )}
                    </div>

                    {/* Metadata & Actions for Assistant */}
                    {msg.role === "assistant" && msg.id !== "streaming-temp" && (
                      <div className="flex items-center justify-between text-xs text-muted-foreground px-1 pt-1">
                        <div className="flex items-center gap-3">
                          {msg.confidence_score !== undefined && (
                            <span className="font-semibold text-[11px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20">
                              Verified Grounding: {Math.round(msg.confidence_score * 100)}%
                            </span>
                          )}
                          {msg.citations && msg.citations.length > 0 && (
                            <button
                              onClick={() => openCitationsPanel(msg.citations || [])}
                              className="flex items-center gap-1 text-primary hover:underline font-semibold text-xs"
                            >
                              <FileText className="h-3.5 w-3.5" />
                              View Citations ({msg.citations.length})
                            </button>
                          )}
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleCopyText(msg.id, msg.content)}
                            className="p-1 hover:text-foreground text-muted-foreground transition-colors"
                            title="Copy Response"
                          >
                            {copiedMsgId === msg.id ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                          </button>
                          <button
                            onClick={() => handleBookmark(msg.id)}
                            className={`p-1 hover:text-primary transition-colors ${msg.is_bookmarked ? "text-primary font-bold" : ""}`}
                            title="Bookmark"
                          >
                            <Bookmark className="h-3.5 w-3.5" />
                          </button>
                          <button onClick={() => handleFeedback(msg.id, 5)} className="p-1 hover:text-emerald-500 transition-colors">
                            <ThumbsUp className="h-3.5 w-3.5" />
                          </button>
                          <button onClick={() => handleFeedback(msg.id, 1)} className="p-1 hover:text-destructive transition-colors">
                            <ThumbsDown className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Follow-up Question suggestions */}
                    {msg.role === "assistant" && msg.suggested_questions && msg.suggested_questions.length > 0 && (
                      <div className="pt-2 pl-1 space-y-1.5">
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold flex items-center gap-1">
                          <HelpCircle className="h-3 w-3" /> Suggested Follow-ups:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {msg.suggested_questions.map((q, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSendMessage(q)}
                              className="bg-card hover:bg-muted text-foreground text-xs px-3 py-1.5 rounded-full border border-border/70 hover:border-primary/30 transition-all text-left shadow-2xs"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Footer Dock */}
          <footer className="p-4 border-t border-border/60 bg-card/90 backdrop-blur-md shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(input);
              }}
              className="flex items-end gap-2 max-w-4xl mx-auto relative"
            >
              <textarea
                rows={1}
                placeholder="Ask PakLaw AI legal copilot (e.g. PPC Section 302 grounds, Constitution Art 199)..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(input);
                  }
                }}
                className="flex-1 bg-background border border-border/80 rounded-2xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-foreground resize-none min-h-[46px] max-h-32"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-primary text-primary-foreground h-[46px] w-[46px] rounded-2xl hover:bg-primary/95 transition-all flex items-center justify-center disabled:opacity-50 shrink-0 shadow-md shadow-primary/15"
              >
                {loading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </button>
            </form>
          </footer>
        </div>

        {/* Citations Collapsible Sidebar */}
        {isCitationOpen && (
          <aside className="w-80 border-l border-border/80 bg-card h-full flex flex-col shrink-0 animate-in slide-in-from-right duration-200">
            <div className="h-16 border-b border-border/60 px-6 flex items-center justify-between">
              <h3 className="font-bold text-sm text-foreground flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" /> Source Citations
              </h3>
              <button
                onClick={() => setIsCitationOpen(false)}
                className="p-1 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-all"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {activeCitations.map((cit) => (
                <div key={cit.id} className="p-3.5 bg-muted/40 rounded-xl border border-border/60 space-y-2 shadow-2xs">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-primary">[{cit.citation_number}] {cit.document_title}</span>
                    {cit.relevance_score !== undefined && (
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full">
                        {Math.round(cit.relevance_score * 100)}% match
                      </span>
                    )}
                  </div>
                  {cit.section_number && (
                    <p className="text-xs font-semibold text-foreground">Section: {cit.section_number} - {cit.section_title || "Untitled"}</p>
                  )}
                  {cit.page_number && (
                    <p className="text-[10px] text-muted-foreground">Page Reference: {cit.page_number}</p>
                  )}
                  {cit.excerpt && (
                    <blockquote className="text-xs text-muted-foreground border-l-2 border-primary/40 pl-2.5 py-0.5 italic leading-relaxed">
                      &quot;{cit.excerpt}&quot;
                    </blockquote>
                  )}
                </div>
              ))}
            </div>
          </aside>
        )}

      </main>
    </div>
  );
}

