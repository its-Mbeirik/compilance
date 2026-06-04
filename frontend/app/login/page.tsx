"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../contexts/auth";

export default function LoginPage() {
  const { login, user, loading } = useAuth();
  const router = useRouter();

  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [busy,     setBusy]     = useState(false);

  // Redirect already-authenticated users
  useEffect(() => {
    if (loading || !user) return;
    if (user.role === "admin")           router.replace("/admin");
    else if (user.status === "pending" || user.status === "rejected")
                                         router.replace("/pending");
    else                                 router.replace("/");
  }, [user, loading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      // redirect handled by the useEffect above
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur de connexion");
      setBusy(false);
    }
  };

  if (loading) return null;

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-full bg-black flex items-center justify-center text-white text-xl font-bold mx-auto mb-3">
            ⚖
          </div>
          <h1 className="text-2xl font-semibold text-neutral-900">ConformIA</h1>
          <p className="text-sm text-neutral-400 mt-1">Assistant de conformité contractuelle</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-neutral-700 mb-1.5">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="vous@exemple.mr"
              className="w-full border border-neutral-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-neutral-400 text-neutral-900 placeholder:text-neutral-300"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-neutral-700 mb-1.5">Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className="w-full border border-neutral-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-neutral-400 text-neutral-900 placeholder:text-neutral-300"
            />
          </div>

          {error && (
            <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full bg-black text-white font-medium py-3 rounded-xl text-sm hover:bg-neutral-800 disabled:bg-neutral-300 transition-colors"
          >
            {busy ? "Connexion…" : "Se connecter"}
          </button>
        </form>

        <p className="text-center text-xs text-neutral-400 mt-6">
          Pas encore de compte ?{" "}
          <Link href="/register" className="text-neutral-900 font-medium underline underline-offset-2">
            S&apos;inscrire
          </Link>
        </p>
      </div>
    </div>
  );
}
