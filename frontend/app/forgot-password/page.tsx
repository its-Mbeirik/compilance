"use client";
import { useState } from "react";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [email,   setEmail]   = useState("");
  const [sent,    setSent]    = useState(false);
  const [error,   setError]   = useState("");
  const [busy,    setBusy]    = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Erreur serveur");
      }
      setSent(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur serveur");
    } finally {
      setBusy(false);
    }
  };

  if (sent) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <div className="w-14 h-14 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center text-2xl mx-auto mb-5">
            ✉
          </div>
          <h2 className="text-xl font-semibold text-neutral-900 mb-2">Email envoyé</h2>
          <p className="text-sm text-neutral-500 mb-6">
            Si <strong>{email}</strong> correspond à un compte, vous recevrez un lien de
            réinitialisation valable <strong>1 heure</strong>.
          </p>
          <p className="text-xs text-neutral-400 mb-4">Vérifiez aussi votre dossier spam.</p>
          <Link href="/login" className="text-sm font-medium text-neutral-900 underline underline-offset-2">
            Retour à la connexion
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-full bg-black flex items-center justify-center text-white text-xl font-bold mx-auto mb-3">
            ⚖
          </div>
          <h1 className="text-2xl font-semibold text-neutral-900">Mot de passe oublié</h1>
          <p className="text-sm text-neutral-400 mt-1">
            Entrez votre email pour recevoir un lien de réinitialisation
          </p>
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
            {busy ? "Envoi…" : "Envoyer le lien"}
          </button>
        </form>

        <p className="text-center text-xs text-neutral-400 mt-6">
          <Link href="/login" className="text-neutral-900 font-medium underline underline-offset-2">
            Retour à la connexion
          </Link>
        </p>
      </div>
    </div>
  );
}
