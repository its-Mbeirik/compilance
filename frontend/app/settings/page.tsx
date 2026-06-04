"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth, useApiFetch } from "../contexts/auth";
import UserSidebar from "../components/UserSidebar";

export default function SettingsPage() {
  const { user, loading } = useAuth();
  const apiFetch = useApiFetch();
  const router = useRouter();

  const [name,      setName]      = useState("");
  const [email,     setEmail]     = useState("");
  const [profMsg,   setProfMsg]   = useState("");
  const [profErr,   setProfErr]   = useState("");
  const [profBusy,  setProfBusy]  = useState(false);

  const [currentPw, setCurrentPw] = useState("");
  const [newPw,     setNewPw]     = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwMsg,     setPwMsg]     = useState("");
  const [pwErr,     setPwErr]     = useState("");
  const [pwBusy,    setPwBusy]    = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user)                      { router.replace("/login");   return; }
    if (user.role === "admin")      { router.replace("/admin");   return; }
    if (user.status !== "approved") { router.replace("/pending"); return; }
    setName(user.name);
    setEmail(user.email);
  }, [user, loading, router]);

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfMsg(""); setProfErr(""); setProfBusy(true);
    try {
      const res = await apiFetch("/api/auth/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), email }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Erreur de mise à jour");
      }
      setProfMsg("Profil mis à jour.");
    } catch (err: unknown) {
      setProfErr(err instanceof Error ? err.message : "Erreur serveur");
    } finally {
      setProfBusy(false);
    }
  };

  const changePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwMsg(""); setPwErr("");
    if (newPw !== confirmPw) { setPwErr("Les mots de passe ne correspondent pas"); return; }
    if (newPw.length < 6)   { setPwErr("Minimum 6 caractères"); return; }
    setPwBusy(true);
    try {
      const res = await apiFetch("/api/auth/password", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Erreur de modification");
      }
      setPwMsg("Mot de passe modifié.");
      setCurrentPw(""); setNewPw(""); setConfirmPw("");
    } catch (err: unknown) {
      setPwErr(err instanceof Error ? err.message : "Erreur serveur");
    } finally {
      setPwBusy(false);
    }
  };

  if (loading || !user) return null;

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      <UserSidebar />

      <main className="flex-1 overflow-y-auto p-8 max-w-xl">
        <h1 className="text-xl font-semibold text-neutral-900 mb-8">Paramètres</h1>

        {/* Profile */}
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-neutral-900 mb-4">Profil</h2>
          <form onSubmit={saveProfile} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-neutral-700 mb-1">Nom complet</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                required
                className="w-full border border-neutral-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-neutral-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-neutral-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="w-full border border-neutral-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-neutral-400"
              />
            </div>
            {profErr && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{profErr}</p>}
            {profMsg && <p className="text-xs text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">{profMsg}</p>}
            <button
              type="submit"
              disabled={profBusy}
              className="bg-black text-white text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-neutral-800 disabled:bg-neutral-300 transition-colors"
            >
              {profBusy ? "Enregistrement…" : "Enregistrer"}
            </button>
          </form>
        </section>

        <div className="border-t border-neutral-100 my-6" />

        {/* Password */}
        <section>
          <h2 className="text-sm font-semibold text-neutral-900 mb-4">Changer le mot de passe</h2>
          <form onSubmit={changePassword} className="space-y-3">
            {[
              { label: "Mot de passe actuel",    value: currentPw, setter: setCurrentPw, autocomplete: "current-password" },
              { label: "Nouveau mot de passe",    value: newPw,     setter: setNewPw,     autocomplete: "new-password" },
              { label: "Confirmer",               value: confirmPw, setter: setConfirmPw, autocomplete: "new-password" },
            ].map(({ label, value, setter, autocomplete }) => (
              <div key={label}>
                <label className="block text-xs font-medium text-neutral-700 mb-1">{label}</label>
                <input
                  type="password"
                  value={value}
                  onChange={e => setter(e.target.value)}
                  required
                  autoComplete={autocomplete}
                  placeholder="••••••••"
                  className="w-full border border-neutral-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-neutral-400"
                />
              </div>
            ))}
            {pwErr && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{pwErr}</p>}
            {pwMsg && <p className="text-xs text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">{pwMsg}</p>}
            <button
              type="submit"
              disabled={pwBusy}
              className="bg-black text-white text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-neutral-800 disabled:bg-neutral-300 transition-colors"
            >
              {pwBusy ? "Modification…" : "Modifier le mot de passe"}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
