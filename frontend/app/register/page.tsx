"use client";
import { useState } from "react";
import Link from "next/link";

export default function RegisterPage() {
  const [name,     setName]     = useState("");
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [confirm,  setConfirm]  = useState("");
  const [error,    setError]    = useState("");
  const [success,  setSuccess]  = useState(false);
  const [busy,     setBusy]     = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Les mots de passe ne correspondent pas");
      return;
    }
    if (password.length < 6) {
      setError("Le mot de passe doit comporter au moins 6 caractères");
      return;
    }
    setBusy(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Erreur lors de l'inscription");
      }
      setSuccess(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur serveur");
    } finally {
      setBusy(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <div className="w-14 h-14 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center text-2xl mx-auto mb-4">
            ✓
          </div>
          <h2 className="text-xl font-semibold text-neutral-900 mb-2">Vérifiez votre email</h2>
          <p className="text-sm text-neutral-500 mb-3">
            Un email de vérification vous a été envoyé. Cliquez sur le lien dans l&apos;email
            pour confirmer votre adresse.
          </p>
          <p className="text-sm text-neutral-400 mb-6">
            Votre compte sera ensuite soumis à l&apos;approbation d&apos;un administrateur.
          </p>
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
          <h1 className="text-2xl font-semibold text-neutral-900">Créer un compte</h1>
          <p className="text-sm text-neutral-400 mt-1">En attente d&apos;approbation administrateur</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {[
            { label: "Nom complet",              value: name,     setter: setName,     type: "text",     placeholder: "Moussa Diallo",   autocomplete: "name" },
            { label: "Email",                    value: email,    setter: setEmail,    type: "email",    placeholder: "vous@exemple.mr", autocomplete: "email" },
            { label: "Mot de passe",             value: password, setter: setPassword, type: "password", placeholder: "Min. 6 caractères", autocomplete: "new-password" },
            { label: "Confirmer le mot de passe", value: confirm,  setter: setConfirm,  type: "password", placeholder: "••••••••",        autocomplete: "new-password" },
          ].map(({ label, value, setter, type, placeholder, autocomplete }) => (
            <div key={label}>
              <label className="block text-xs font-medium text-neutral-700 mb-1.5">{label}</label>
              <input
                type={type}
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
            <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full bg-black text-white font-medium py-3 rounded-xl text-sm hover:bg-neutral-800 disabled:bg-neutral-300 transition-colors"
          >
            {busy ? "Inscription…" : "S'inscrire"}
          </button>
        </form>

        <p className="text-center text-xs text-neutral-400 mt-6">
          Déjà un compte ?{" "}
          <Link href="/login" className="text-neutral-900 font-medium underline underline-offset-2">
            Se connecter
          </Link>
        </p>
      </div>
    </div>
  );
}
