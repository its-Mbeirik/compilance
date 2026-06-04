"use client";
import { useEffect, useState, useCallback } from "react";
import { useApiFetch } from "../../contexts/auth";

interface PendingUser {
  id:         string;
  name:       string;
  email:      string;
  created_at: string | null;
}

const fmt = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString("fr-FR") : "—";

export default function PendingApprovalsPage() {
  const apiFetch = useApiFetch();
  const [users,   setUsers]   = useState<PendingUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy,    setBusy]    = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    apiFetch("/api/admin/pending")
      .then(r => r.ok ? r.json() : [])
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, [apiFetch]);

  useEffect(load, [load]);

  const action = async (id: string, act: "approve" | "reject") => {
    setBusy(id);
    await apiFetch(`/api/admin/users/${id}/${act}`, { method: "POST" }).catch(() => {});
    setBusy(null);
    load();
  };

  return (
    <div>
      <h1 className="text-xl font-semibold text-neutral-900 mb-1">Approbations en attente</h1>
      <p className="text-sm text-neutral-400 mb-6">
        {loading
          ? "Chargement…"
          : `${users.length} compte${users.length !== 1 ? "s" : ""} en attente`}
      </p>

      {!loading && users.length === 0 ? (
        <div className="bg-neutral-50 border border-neutral-200 rounded-xl p-10 text-center">
          <p className="text-sm text-neutral-400">Aucun compte en attente d&apos;approbation.</p>
        </div>
      ) : (
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-neutral-900 text-white">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium tracking-wide">Nom</th>
                <th className="px-4 py-3 text-left text-xs font-medium tracking-wide">Email</th>
                <th className="px-4 py-3 text-left text-xs font-medium tracking-wide">Inscrit le</th>
                <th className="px-4 py-3 text-right text-xs font-medium tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {users.map(u => (
                <tr key={u.id} className="hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-neutral-900">{u.name}</td>
                  <td className="px-4 py-3 text-neutral-500">{u.email}</td>
                  <td className="px-4 py-3 text-neutral-400 text-xs">{fmt(u.created_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => action(u.id, "approve")}
                        disabled={busy === u.id}
                        className="bg-black text-white text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-neutral-800 disabled:bg-neutral-300 transition-colors"
                      >
                        Approuver
                      </button>
                      <button
                        onClick={() => action(u.id, "reject")}
                        disabled={busy === u.id}
                        className="border border-red-200 text-red-600 text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-red-50 disabled:opacity-40 transition-colors"
                      >
                        Refuser
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
