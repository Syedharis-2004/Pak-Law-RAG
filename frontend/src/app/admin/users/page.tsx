"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/sidebar";
import { Users, Search, Plus, MoreVertical, Shield, ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface User {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  created_at: string;
}

export default function UsersAdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        // Mock data for UI demonstration since API might not have this endpoint fully populated
        setUsers([
          { id: "usr_1", email: "admin@paklaw.ai", full_name: "System Admin", roles: ["admin", "super_admin"], is_active: true, created_at: "2024-01-01T10:00:00Z" },
          { id: "usr_2", email: "ali.khan@lawfirm.pk", full_name: "Ali Khan", roles: ["lawyer", "user"], is_active: true, created_at: "2024-02-15T14:30:00Z" },
          { id: "usr_3", email: "zara.ahmed@court.pk", full_name: "Zara Ahmed", roles: ["judge"], is_active: true, created_at: "2024-03-10T09:15:00Z" },
          { id: "usr_4", email: "suspended@test.com", full_name: "Test User", roles: ["user"], is_active: false, created_at: "2024-04-05T16:45:00Z" },
        ]);
      } catch (err) {
        console.error("Failed to load users", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchUsers();
  }, []);

  const filteredUsers = users.filter(u => 
    u.full_name.toLowerCase().includes(search.toLowerCase()) || 
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <header className="h-16 border-b border-border bg-card px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" />
            <h2 className="font-semibold text-foreground">User Management</h2>
          </div>
          <button className="flex items-center gap-2 bg-primary text-primary-foreground px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-primary/90 transition-all">
            <Plus className="h-4 w-4" />
            Invite User
          </button>
        </header>

        <div className="flex-1 p-6 overflow-y-auto">
          <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden flex flex-col">
            {/* Toolbar */}
            <div className="p-4 border-b border-border flex items-center justify-between gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search users by name or email..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-background border border-border rounded-lg text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
                />
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b border-border">
                  <tr>
                    <th className="px-6 py-3 font-medium">Name</th>
                    <th className="px-6 py-3 font-medium">Roles</th>
                    <th className="px-6 py-3 font-medium">Status</th>
                    <th className="px-6 py-3 font-medium">Joined</th>
                    <th className="px-6 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {loading ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-muted-foreground">
                        Loading users...
                      </td>
                    </tr>
                  ) : filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-muted-foreground">
                        No users found
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((user) => (
                      <tr key={user.id} className="hover:bg-muted/30 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
                              {user.full_name.charAt(0)}
                            </div>
                            <div>
                              <p className="font-medium text-foreground">{user.full_name}</p>
                              <p className="text-xs text-muted-foreground">{user.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex gap-1 flex-wrap">
                            {user.roles.map(r => (
                              <span key={r} className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${r.includes('admin') ? 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20' : 'bg-muted text-muted-foreground border-border'}`}>
                                {r}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          {user.is_active ? (
                            <span className="flex items-center gap-1.5 text-xs text-emerald-600 bg-emerald-500/10 px-2 py-1 rounded-full w-fit font-medium">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Active
                            </span>
                          ) : (
                            <span className="flex items-center gap-1.5 text-xs text-red-600 bg-red-500/10 px-2 py-1 rounded-full w-fit font-medium">
                              <span className="h-1.5 w-1.5 rounded-full bg-red-500" /> Suspended
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-muted-foreground">
                          {formatDate(user.created_at)}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button className="text-muted-foreground hover:text-foreground transition-colors p-1.5 rounded-md hover:bg-muted">
                            <MoreVertical className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
