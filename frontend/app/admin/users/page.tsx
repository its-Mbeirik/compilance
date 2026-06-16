"use client";
import { useEffect, useState, useMemo, useCallback } from "react";
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

interface AdminLog {
  id:             string;
  admin_name:     string;
  target_name:    string;
  action:         string;
  old_status:     string | null;
  new_status:     string;
  created_at:     string | null;
}

type FilterTab = "all" | "approved" | "disabled" | "pending";

const TABS: { key: FilterTab; label: string }[] = [
  { key: "all",      label: "Tous"       },
  { key: "approved", label: "Actifs"     },
  { key: "disabled", label: "Désactivés" },
  { key: "pending",  label: "En attente" },
];

const STATUS_LABEL: Record<string, string> = {
  approved: "Actif",
  disabled: "Désactivé",
  pending:  "En attente",
  rejected: "Rejeté",
};

const STATUS_CLS: Record<string, string> = {
  approved: "bg-emerald-50 text-emerald-700",
  disabled: "bg-red-50 text-red-700",
  pending:  "bg-amber-50 text-amber-700",
  rejected: "bg-neutral-100 text-neutral-500",
};

const ACTION_LABEL: Record<string, string> = {
  disable: "Désactivation",
  enable:  "Réactivation",
  approve: "Approbation",
  reject:  "Rejet",
};

const ACTION_CLS: Record<string, string> = {
  disable: "bg-red-50 text-red-700",
  enable:  "bg-emerald-50 text-emerald-700",
  approve: "bg-blue-50 text-blue-700",
  reject:  "bg-neutral-100 text-neutral-500",
};

const fmt = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString("fr-FR") : "—";

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[status] ?? "bg-neutral-100 text-neutral-500"}`}>
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

function TabBar({ tab, setTab }: { tab: FilterTab; setTab: (t: FilterTab) => void }) {
  return (
    <div className="flex gap-1 mb-3 flex-wrap">
      {TABS.map(t => (
        <button
          key={t.key}
          onClick={() => setTab(t.key)}
          className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
            tab === t.key
              ? "bg-neutral-900 text-white"
              : "bg-neutral-100 text-neutral-500 hover:bg-neutral-200"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export default function UserManagementPage() {
  const apiFetch = useApiFetch();
  const [users,     setUsers]     = useState<ManagedUser[]>([]);
  const [logs,      setLogs]      = useState<AdminLog[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [search,    setSearch]    = useState("");
  const [tabMain,   setTabMain]   = useState<FilterTab>("all");
  const [tabSub,    setTabSub]    = useState<FilterTab>("all");
  const [modalUser, setModalUser] = useState<ManagedUser | null>(null);
  const [modalBusy, setModalBusy] = useState(false);

  const fetchAll = useCallback(() => {
    Promise.all([
      apiFetch("/api/admin/users").then(r => r.ok ? r.json() : []),
      apiFetch("/api/admin/logs").then(r => r.ok ? r.json() : []),
    ])
      .then(([u, l]) => { setUsers(u); setLogs(l); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [apiFetch]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const mainUsers = useMemo(() => users.filter(u => u.role === "user"),     [users]);
  const subUsers  = useMemo(() => users.filter(u => u.role === "sub_user"), [users]);

  const filteredMain = useMemo(() => {
    const q = search.toLowerCase();
    return mainUsers
      .filter(u => tabMain === "all" || u.status === tabMain)
      .filter(u => !q || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
  }, [mainUsers, tabMain, search]);

  const filteredSub = useMemo(() => {
    const q = search.toLowerCase();
    return subUsers
      .filter(u => tabSub === "all" || u.status === tabSub)
      .filter(u => !q || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
  }, [subUsers, tabSub, search]);

  const parentName = (pid: string | null) => {
    const p = users.find(u => u.id === pid);
    return p ? p.name : "—";
  };

  const closeModal = () => { if (!modalBusy) setModalUser(null); };

  const toggleStatus = async () => {
    if (!modalUser) return;
    const action = modalUser.status === "approved" ? "disable" : "enable";
    setModalBusy(true);
    try {
      const res = await apiFetch(`/api/admin/users/${modalUser.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      if (res.ok) { setModalUser(null); fetchAll(); }
    } catch { /* ignore */ } finally {
      setModalBusy(false);
    }
  };

  const ToggleBtn = ({ u }: { u: ManagedUser }) => {
    if (u.status !== "approved" && u.status !== "disabled") return null;
    return (
      <button
        onClick={() => setModalUser(u)}
        className={`text-xs px-3 py-1 rounded-lg font-medium transition-colors ${
          u.status === "approved"
            ? "bg-red-50 text-red-700 hover:bg-red-100"
            : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
        }`}
      >
        {u.status === "approved" ? "Désactiver" : "Réactiver"}
      </button>
    );
  };

  return (
    <div>
      <h1 className="text-xl font-semibold text-neutral-900 mb-1">Gestion des utilisateurs</h1>
      <p className="text-sm text-neutral-400 mb-6">
        {loading
          ? "Chargement…"
          : `${mainUsers.length} utilisateur${mainUsers.length !== 1 ? "s" : ""} · ${subUsers.length} assistant${subUsers.length !== 1 ? "s" : ""}`}
      </p>

      {/* Search */}
      <div className="mb-6">
        <input
          type="search"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Rechercher par nom ou email…"
          className="w-full max-w-sm border border-neutral-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-neutral-400 bg-white"
        />
      </div>

      {/* ── Utilisateurs ── */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-neutral-700 mb-3">Utilisateurs</h2>
        <TabBar tab={tabMain} setTab={setTabMain} />
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-neutral-900 text-white">
              <tr>
                {["Nom", "Email", "Statut", "Inscrit le", "Assistants", "Action"].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {filteredMain.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-xs text-neutral-400">Aucun utilisateur</td>
                </tr>
              ) : filteredMain.map(u => (
                <tr key={u.id} className="hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-neutral-900">{u.name}</td>
                  <td className="px-4 py-3 text-neutral-500">{u.email}</td>
                  <td className="px-4 py-3"><StatusBadge status={u.status} /></td>
                  <td className="px-4 py-3 text-xs text-neutral-400">{fmt(u.created_at)}</td>
                  <td className="px-4 py-3 text-xs text-neutral-400">{subUsers.filter(s => s.parent_id === u.id).length}</td>
                  <td className="px-4 py-3"><ToggleBtn u={u} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Assistants ── */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-neutral-700 mb-3">Assistants</h2>
        <TabBar tab={tabSub} setTab={setTabSub} />
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-neutral-900 text-white">
              <tr>
                {["Nom", "Email", "Statut", "Utilisateur parent", "Créé le", "Action"].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {filteredSub.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-xs text-neutral-400">Aucun assistant</td>
                </tr>
              ) : filteredSub.map(u => (
                <tr key={u.id} className="hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-neutral-900">{u.name}</td>
                  <td className="px-4 py-3 text-neutral-500">{u.email}</td>
                  <td className="px-4 py-3"><StatusBadge status={u.status} /></td>
                  <td className="px-4 py-3 text-xs text-neutral-500">{parentName(u.parent_id)}</td>
                  <td className="px-4 py-3 text-xs text-neutral-400">{fmt(u.created_at)}</td>
                  <td className="px-4 py-3"><ToggleBtn u={u} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Journal des actions ── */}
      <section>
        <h2 className="text-sm font-semibold text-neutral-700 mb-3">Journal des actions admin</h2>
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-neutral-900 text-white">
              <tr>
                {["Administrateur", "Utilisateur cible", "Action", "Statut précédent", "Nouveau statut", "Date"].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-xs text-neutral-400">Aucune action enregistrée</td>
                </tr>
              ) : logs.map(l => (
                <tr key={l.id} className="hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-neutral-900">{l.admin_name}</td>
                  <td className="px-4 py-3 text-neutral-600">{l.target_name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ACTION_CLS[l.action] ?? "bg-neutral-100 text-neutral-500"}`}>
                      {ACTION_LABEL[l.action] ?? l.action}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {l.old_status
                      ? <StatusBadge status={l.old_status} />
                      : <span className="text-xs text-neutral-400">—</span>}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={l.new_status} /></td>
                  <td className="px-4 py-3 text-xs text-neutral-400">{fmt(l.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── Confirmation modal ── */}
      {modalUser && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
          onClick={closeModal}
        >
          <div
            className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-xl mx-4"
            onClick={e => e.stopPropagation()}
          >
            <h3 className="text-base font-semibold text-neutral-900 mb-2">
              {modalUser.status === "approved" ? "Désactiver ce compte" : "Réactiver ce compte"}
            </h3>
            <p className="text-sm text-neutral-500 mb-6">
              {modalUser.status === "approved"
                ? `Êtes-vous sûr de vouloir désactiver le compte de ${modalUser.name} ? L'utilisateur sera immédiatement déconnecté.`
                : `Êtes-vous sûr de vouloir réactiver le compte de ${modalUser.name} ?`}
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={closeModal}
                disabled={modalBusy}
                className="text-sm px-4 py-2 rounded-lg border border-neutral-200 text-neutral-700 hover:bg-neutral-50 disabled:opacity-50 transition-colors"
              >
                Annuler
              </button>
              <button
                onClick={toggleStatus}
                disabled={modalBusy}
                className={`text-sm px-4 py-2 rounded-lg font-medium text-white disabled:opacity-50 transition-colors ${
                  modalUser.status === "approved" ? "bg-red-600 hover:bg-red-700" : "bg-emerald-600 hover:bg-emerald-700"
                }`}
              >
                {modalBusy ? "…" : modalUser.status === "approved" ? "Désactiver" : "Réactiver"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
