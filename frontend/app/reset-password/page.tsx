"use client";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

function ResetPasswordContent() {
  const params = useSearchParams();
  const router = useRouter();
  const token  = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm,  setConfirm]  = useState("");
  const [error,    setError]    = useState("");
  const [busy,     setBusy]     = useState(false);

  if (!token) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <div className="w-14 h-14 rounded-full bg-red-50 border border-red-100 flex items-center justify-center text-2xl mx-auto mb-5">✕</div>
          <h2 className="text-xl font-semibold text-neutral-900 mb-2">Lien invalide</h2>
          <p className="text-sm text-neutral-500 mb-6">Aucun token de réinitialisation trouvé dans l&apos;URL.</p>
          <Link href="/forgot-password" className="text-sm font-medium text-neutral-900 underline underline-offset-2">
            Demander un nouveau lien
          </Link>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) { setError("Les mots de passe ne correspondent pas"); return; }
    if (password.length < 6)  { setError("Le mot de passe doit comporter au moins 6 caractères"); return; }
    setBusy(true);
    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Erreur serveur");
      }
      router.replace("/login?reset=1");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur serveur");
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-full bg-black flex items-center justify-center text-white text-xl font-bold mx-auto mb-3">⚖</div>
          <h1 className="text-2xl font-semibold text-neutral-900">Nouveau mot de passe</h1>
          <p className="text-sm text-neutral-400 mt-1">Choisissez un mot de passe sécurisé</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {[
            { label: "Nouveau mot de passe",      value: password, setter: setPassword, placeholder: "Min. 6 caractères", autocomplete: "new-password" },
            { label: "Confirmer le mot de passe", value: confirm,  setter: setConfirm,  placeholder: "••••••••",          autocomplete: "new-password" },
          ].map(({ label, value, setter, placeholder, autocomplete }) => (
            <div key={label}>
              <label className="block text-xs font-medium text-neutral-700 mb-1.5">{label}</label>
              <input
                type="password"
                value={value}
                onChange={e => setter(e.target.value)}
                required
                autoComplete={autocomplete}
                placeholder={placeholder}
                className="w-full border border-neutral-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-neutral-400 text-neutral-900 placeholder:text-neutral-300"
              />
            </div>
          ))}

          {error && (
            <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full bg-black text-white font-medium py-3 rounded-xl text-sm hover:bg-neutral-800 disabled:bg-neutral-300 transition-colors"
          >
            {busy ? "Réinitialisation…" : "Réinitialiser le mot de passe"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordContent />
    </Suspense>
  );
}
