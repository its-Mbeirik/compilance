"use client";
import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

export type UserRole   = "admin" | "user" | "sub_user";
export type UserStatus = "pending" | "approved" | "rejected";

export interface AuthUser {
  id:         string;
  email:      string;
  name:       string;
  role:       UserRole;
  status:     UserStatus;
  parent_id?: string | null;
}

interface AuthCtx {
  user:    AuthUser | null;
  token:   string | null;
  loading: boolean;
  login:   (email: string, password: string) => Promise<void>;
  logout:  () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user,    setUser]    = useState<AuthUser | null>(null);
  const [token,   setToken]   = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("auth_token");
    if (!stored) { setLoading(false); return; }
    setToken(stored);
    fetch("/api/auth/me", { headers: { Authorization: `Bearer ${stored}` } })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) setUser(data);
        else { localStorage.removeItem("auth_token"); setToken(null); }
      })
      .catch(() => { localStorage.removeItem("auth_token"); setToken(null); })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? "Erreur de connexion");
    }
    const data = await res.json();
    localStorage.setItem("auth_token", data.token);
    setToken(data.token);
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("auth_token");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <Ctx.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth(): AuthCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

/** Returns a fetch wrapper that automatically injects the Bearer token. */
export function useApiFetch() {
  return useCallback((url: string, init: RequestInit = {}) => {
    const t = localStorage.getItem("auth_token");
    return fetch(url, {
      ...init,
      headers: {
        ...(init.headers ?? {}),
        ...(t ? { Authorization: `Bearer ${t}` } : {}),
      },
    });
  }, []);
}
