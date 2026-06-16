"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth, useApiFetch } from "../contexts/auth";
import UserSidebar from "../components/UserSidebar";

interface SubUser {
  id:         string;
  name:       string;
  email:      string;
  created_at: string | null;
}

const fmt = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString("fr-FR") : "—";

export default function SubUsersPage() {
  const { user, loading } = useAuth();
  const apiFetch = useApiFetch();
  const router = useRouter();

  const [subUsers,        setSubUsers]        = useState<SubUser[]>([]);
  const [name,            setName]            = useState("");
  const [email,           setEmail]           = useState("");
  const [password,        setPassword]        = useState("");
  const [parentPassword,  setParentPassword]  = useState("");
  const [error,           setError]           = useState("");
  const [success,         setSuccess]         = useState("");
  const [busy,            setBusy]            = useState(false);

  // Route guard
  useEffect(() => {
    if (loading) return;
    if (!user)                      { router.replace("/login");   return; }
    if (user.role === "admin")      { router.replace("/admin");   return; }
    if (user.status !== "approved") { router.replace("/pending"); return; }
    if (user.role !== "user")       { router.replace("/");        return; }
  }, [user, loading, router]);

  const load = useCallback(() => {
    apiFetch("/api/users/sub-users")
      .then(r => r.ok ? r.json() : [])
      .then(setSubUsers)
      .catch(() => {});
  }, [apiFetch]);

  useEffect(load, [load]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setSuccess("");
    if (password.length < 6)       { setError("Le mot de passe de l'assistant doit comporter au moins 6 caractères"); return; }
    if (!parentPassword)           { setError("Veuillez entrer votre mot de passe pour confirmer"); return; }
    setBusy(true);
    try {
      const res = await apiFetch("/api/users/sub-users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), email, password, parent_password: parentPassword }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Erreur serveur");
      }
      setName(""); setEmail(""); setPassword(""); setParentPassword("");
      setSuccess("Assistant créé avec succès.");
      load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur serveur");
    } finally {
      setBusy(false);
    }
  };

  if (loading || !user) return null;

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      <UserSidebar />

      <main className="flex-1 overflow-y-auto p-8">
        <h1 className="text-xl font-semibold text-neutral-900 mb-6">Assistants</h1>

        {/* Create form */}
        <div className="bg-neutral-50 border border-neutral-200 rounded-xl p-6 mb-8 max-w-md">
          <h2 className="text-sm font-semibold text-neutral-900 mb-4">Créer un assistant</h2>
          <form onSubmit={create} className="space-y-3">
            {/* Sub-user fields */}
            {[
              { label: "Nom complet",              value: name,     setter: setName,     type: "text",     placeholder: "Prénom Nom",        autocomplete: "off" },
              { label: "Email",                    value: email,    setter: setEmail,    type: "email",    placeholder: "email@exemple.mr",  autocomplete: "off" },
              { label: "Mot de passe (assistant)", value: password, setter: setPassword, type: "password", placeholder: "Min. 6 caractères", autocomplete: "new-password" },
            ].map(({ label, value, setter, type, placeholder, autocomplete }) => (
              <div key={label}>
                <label className="block text-xs font-medium text-neutral-700 mb-1">{label}</label>
                <input
                  type={type}
                  value={value}
                  onChange={e => setter(e.target.value)}
                  required
                  autoComplete={autocomplete}
                  placeholder={placeholder}
                  className="w-full border border-neutral-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-neutral-400 bg-white"
                />
              </div>
            ))}

            {/* Separator */}
            <div className="border-t border-neutral-200 pt-3">
              <label className="block text-xs font-medium text-neutral-700 mb-1">
                Votre mot de passe
                <span className="ml-1 text-neutral-400 font-normal">(confirmation requise)</span>
              </label>
              <input
                type="password"
                value={parentPassword}
                onChange={e => setParentPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full border border-neutral-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-neutral-400 bg-white"
              />
            </div>

            {error   && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
            {success && <p className="text-xs text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">{success}</p>}
            <button
              type="submit"
              disabled={busy}
              className="w-full bg-black text-white text-sm font-medium py-2.5 rounded-lg hover:bg-neutral-800 disabled:bg-neutral-300 transition-colors"
            >
              {busy ? "Création…" : "Créer l'assistant"}
            </button>
          </form>
        </div>

        {/* List */}
        <h2 className="text-sm font-semibold text-neutral-700 mb-3">
          Mes assistants ({subUsers.length})
        </h2>

        {subUsers.length === 0 ? (
          <p className="text-sm text-neutral-400">Aucun assistant pour le moment.</p>
        ) : (
          <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden max-w-2xl">
            <table className="w-full text-sm">
              <thead className="bg-neutral-900 text-white">
                <tr>
                  {["Nom", "Email", "Créé le"].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {subUsers.map(u => (
                  <tr key={u.id} className="hover:bg-neutral-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-neutral-900">{u.name}</td>
                    <td className="px-4 py-3 text-neutral-500">{u.email}</td>
                    <td className="px-4 py-3 text-xs text-neutral-400">{fmt(u.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
