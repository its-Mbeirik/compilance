"use client";
import { useEffect, useState } from "react";
import { useApiFetch } from "../../contexts/auth";

interface ManagedUser {
  id:         string;
  name:       string;
  email:      string;
  role:       string;
  status:     string;
  parent_id:  string | null;
  created_at: string | null;
}

const STATUS_STYLE: Record<string, string> = {
  approved: "bg-emerald-50 text-emerald-700",
  pending:  "bg-amber-50 text-amber-700",
  rejected: "bg-red-50 text-red-700",
};

const fmt = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString("fr-FR") : "—";

export default function UserManagementPage() {
  const apiFetch = useApiFetch();
  const [users,   setUsers]   = useState<ManagedUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/api/admin/users")
      .then(r => r.ok ? r.json() : [])
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, [apiFetch]);

  const mainUsers = users.filter(u => u.role === "user");
  const subUsers  = users.filter(u => u.role === "sub_user");

  const parentName = (pid: string | null) => {
    const p = users.find(u => u.id === pid);
    return p ? p.name : (pid?.slice(0, 8) ?? "—");
  };

  return (
    <div>
      <h1 className="text-xl font-semibold text-neutral-900 mb-1">Gestion des utilisateurs</h1>
      <p className="text-sm text-neutral-400 mb-6">
        {loading
          ? "Chargement…"
          : `${mainUsers.length} utilisateur${mainUsers.length !== 1 ? "s" : ""} · ${subUsers.length} sous-utilisateur${subUsers.length !== 1 ? "s" : ""}`}
      </p>

      {/* Users */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-neutral-700 mb-3">Utilisateurs</h2>
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-neutral-900 text-white">
              <tr>
                {["Nom", "Email", "Statut", "Inscrit le", "Sous-utilisateurs"].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {mainUsers.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-xs text-neutral-400">
                    Aucun utilisateur
                  </td>
                </tr>
              ) : mainUsers.map(u => (
                <tr key={u.id} className="hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-neutral-900">{u.name}</td>
                  <td className="px-4 py-3 text-neutral-500">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLE[u.status] ?? ""}`}>
                      {u.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-400">{fmt(u.created_at)}</td>
                  <td className="px-4 py-3 text-xs text-neutral-400">
                    {subUsers.filter(s => s.parent_id === u.id).length}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Sub-users */}
      <section>
        <h2 className="text-sm font-semibold text-neutral-700 mb-3">Sous-utilisateurs</h2>
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-neutral-900 text-white">
              <tr>
                {["Nom", "Email", "Utilisateur parent", "Créé le"].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {subUsers.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-xs text-neutral-400">
                    Aucun sous-utilisateur
                  </td>
                </tr>
              ) : subUsers.map(u => (
                <tr key={u.id} className="hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-neutral-900">{u.name}</td>
                  <td className="px-4 py-3 text-neutral-500">{u.email}</td>
                  <td className="px-4 py-3 text-xs text-neutral-500">{parentName(u.parent_id)}</td>
                  <td className="px-4 py-3 text-xs text-neutral-400">{fmt(u.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
