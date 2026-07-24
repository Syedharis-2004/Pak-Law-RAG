"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  Scale, 
  MessageSquare, 
  Search, 
  FileText, 
  Database, 
  LogOut,
  Moon,
  Sun,
  ShieldCheck,
  UserCheck,
  Sparkles
} from "lucide-react";
import { useTheme } from "next-themes";
import { clsx } from "clsx";

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, setTheme } = useTheme();

  const menuItems = [
    { name: "Legal Copilot", href: "/chat", icon: MessageSquare, badge: "AI Assistant" },
    { name: "Advanced Search", href: "/search", icon: Search },
    { name: "Research Hub", href: "/research", icon: FileText },
    { name: "Document Library", href: "/documents", icon: Database },
    { name: "Admin Console", href: "/admin", icon: ShieldCheck },
  ];

  const handleLogout = () => {
    localStorage.removeItem("paklaw_token");
    router.push("/auth/login");
  };

  return (
    <aside className="w-64 border-r border-border/80 bg-card/95 backdrop-blur-md flex flex-col h-screen sticky top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-6 border-b border-border/60">
        <Link href="/chat" className="flex items-center gap-3 group">
          <div className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary group-hover:scale-105 transition-transform duration-200 shadow-sm">
            <Scale className="h-5 w-5" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight text-foreground block leading-tight">PakLaw AI</span>
            <span className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400 tracking-wider uppercase flex items-center gap-1">
              <Sparkles className="h-2.5 w-2.5" /> Enterprise
            </span>
          </div>
        </Link>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 mb-2 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
          Workspace Navigation
        </div>

        {menuItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "group flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                isActive 
                  ? "bg-primary text-primary-foreground shadow-md shadow-primary/10 font-semibold" 
                  : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
              )}
            >
              <div className="flex items-center gap-3">
                <item.icon className={clsx("h-4 w-4 transition-transform duration-200 group-hover:scale-110", isActive ? "text-primary-foreground" : "text-muted-foreground")} />
                <span>{item.name}</span>
              </div>
              {item.badge && !isActive && (
                <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full font-medium">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User Info & Quick Controls */}
      <div className="p-3 border-t border-border/60 space-y-2 bg-muted/20">
        <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-card border border-border/60 shadow-xs">
          <div className="h-8 w-8 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400 font-bold text-xs">
            PA
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-foreground truncate">PakLaw Counsel</p>
            <p className="text-[10px] text-muted-foreground truncate">Verified Lawyer Mode</p>
          </div>
          <UserCheck className="h-3.5 w-3.5 text-emerald-500" />
        </div>

        <div className="grid grid-cols-2 gap-1.5 pt-1">
          {/* Theme Toggle */}
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-all duration-150 border border-border/50"
            title="Toggle theme"
          >
            <Sun className="h-3.5 w-3.5 dark:hidden text-amber-500" />
            <Moon className="h-3.5 w-3.5 hidden dark:block text-emerald-400" />
            <span>Theme</span>
          </button>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-destructive hover:bg-destructive/10 transition-all duration-150 border border-destructive/20"
            title="Log Out"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
export default Sidebar;

