"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth, useApiFetch } from "../contexts/auth";

type ArchiveItem = {
  id: string;
  analysis_id: string | null;
  title: string;
  doc_type: string;
  original_file_id: string | null;
  corrected_file_id: string | null;
  archived_at: string;
  original_name: string | null;
  corrected_name: string | null;
};

function DocTypeLabel({ type }: { type: string }) {
  const map: Record<string, { label: string; color: string }> = {
    contrat_travail: { label: "Contrat de travail", color: "bg-blue-50 text-blue-700 ring-1 ring-blue-200" },
    statuts:         { label: "Statuts",            color: "bg-purple-50 text-purple-700 ring-1 ring-purple-200" },
  };
  const entry = map[type] ?? { label: type, color: "bg-neutral-100 text-neutral-600 ring-1 ring-neutral-200" };
  return (
    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${entry.color}`}>
      {entry.label}
    </span>
  );
}

function DownloadButton({
  fileId,
  filename,
  label,
  icon,
}: {
  fileId: string;
  filename: string;
  label: string;
  icon: "original" | "corrected";
}) {
  const apiFetch = useApiFetch();
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`/api/files/doc/${fileId}`);
      if (!res.ok) { alert("Fichier non disponible."); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch { alert("Erreur lors du téléchargement."); }
    finally { setLoading(false); }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={loading}
      className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 ${
        icon === "corrected"
          ? "bg-black text-white hover:bg-neutral-800"
          : "border border-neutral-200 text-neutral-700 hover:bg-neutral-50"
      }`}
    >
      {loading ? (
        <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      ) : (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      )}
      {label}
    </button>
  );
}

function ArchiveCard({ item }: { item: ArchiveItem }) {
  const fmtDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("fr-FR", {
        day: "2-digit", month: "long", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      });
    } catch { return iso; }
  };

  return (
    <div className="bg-white border border-neutral-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-neutral-100 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5 text-neutral-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1 12a2 2 0 002 2h8a2 2 0 002-2L19 8" />
          </svg>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="text-sm font-semibold text-neutral-900 truncate">{item.title || "Sans titre"}</h3>
            {item.doc_type && <DocTypeLabel type={item.doc_type} />}
          </div>
          <p className="text-xs text-neutral-400">{fmtDate(item.archived_at)}</p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-neutral-100 flex items-center gap-2 flex-wrap">
        {item.original_file_id ? (
          <DownloadButton
            fileId={item.original_file_id}
            filename={item.original_name ?? "contrat_original.pdf"}
            label="Contrat original"
            icon="original"
          />
        ) : (
          <span className="flex items-center gap-1.5 text-xs text-neutral-400 border border-neutral-200 px-3 py-1.5 rounded-lg cursor-not-allowed">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            Original indisponible
          </span>
        )}

        {item.corrected_file_id ? (
          <DownloadButton
            fileId={item.corrected_file_id}
            filename={item.corrected_name ?? "contrat_corrige.docx"}
            label="Version corrigée"
            icon="corrected"
          />
        ) : (
          <span className="flex items-center gap-1.5 text-xs text-neutral-400 border border-neutral-200 px-3 py-1.5 rounded-lg cursor-not-allowed">
            Pas de version corrigée
          </span>
        )}

        {item.analysis_id && (
          <Link
            href="/"
            className="ml-auto text-xs text-neutral-400 hover:text-neutral-700 transition-colors underline underline-offset-2"
          >
            Voir l&apos;analyse
          </Link>
        )}
      </div>
    </div>
  );
}

export default function ArchivePage() {
  const { user, loading, logout } = useAuth();
  const apiFetch = useApiFetch();
  const router = useRouter();

  const [archives, setArchives] = useState<ArchiveItem[]>([]);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!user)                      { router.replace("/login");   return; }
    if (user.role === "admin")      { router.replace("/admin");   return; }
    if (user.status !== "approved") { router.replace("/pending"); return; }
  }, [user, loading, router]);

  const fetchArchives = useCallback(async () => {
    setFetching(true);
    setError(null);
    try {
      const res = await apiFetch("/api/archives");
      if (!res.ok) throw new Error("Erreur lors du chargement des archives");
      setArchives(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    } finally {
      setFetching(false);
    }
  }, [apiFetch]);

  useEffect(() => {
    if (user && user.status === "approved" && user.role !== "admin") {
      fetchArchives();
    }
  }, [user, fetchArchives]);

  if (loading || !user) return null;

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-[#111] flex flex-col shrink-0 h-full hidden lg:flex">
        <div className="px-4 py-5 border-b border-white/10 flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-white flex items-center justify-center text-black text-xs font-bold shrink-0">
            ⚖
          </div>
          <div>
            <p className="text-white text-sm font-semibold leading-none">ConformIA</p>
            <p className="text-white/40 text-[10px] mt-0.5">Assistant juridique</p>
          </div>
        </div>

        <div className="px-3 pt-4 pb-2">
          <Link
            href="/"
            className="w-full flex items-center gap-2 text-white/80 hover:text-white hover:bg-white/10 text-sm px-3 py-2.5 rounded-lg transition-colors font-medium"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            Conversations
          </Link>
        </div>

        <div className="flex-1" />

        <div className="px-4 py-4 border-t border-white/10 shrink-0">
          <p className="text-white/40 text-xs truncate mb-1">{user.name}</p>
          <div className="text-[10px] bg-white/10 text-white/50 px-2 py-0.5 rounded-full w-fit mb-2">
            {user.role === "sub_user" ? "Assistant" : "Utilisateur"}
          </div>
          <div className="flex flex-col gap-1">
            {user.role === "user" && (
              <a href="/sub-users" className="text-xs text-white/40 hover:text-white transition-colors">
                Assistants
              </a>
            )}
            <a href="/archive" className="text-xs text-white font-medium flex items-center gap-1.5">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1 12a2 2 0 002 2h8a2 2 0 002-2L19 8" />
              </svg>
              Archive
            </a>
            <a href="/settings" className="text-xs text-white/40 hover:text-white transition-colors">
              Paramètres
            </a>
            <button onClick={logout} className="text-xs text-white/40 hover:text-white transition-colors text-left mt-1">
              Déconnexion
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-white border-b border-neutral-100 px-6 flex items-center gap-3 shrink-0">
          <div className="w-7 h-7 rounded-lg bg-neutral-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-neutral-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1 12a2 2 0 002 2h8a2 2 0 002-2L19 8" />
            </svg>
          </div>
          <h1 className="text-sm font-semibold text-neutral-900">Archive</h1>
          <span className="text-neutral-300 text-xs">·</span>
          <span className="text-xs text-neutral-400">{archives.length} document{archives.length !== 1 ? "s" : ""}</span>
          <button
            onClick={fetchArchives}
            disabled={fetching}
            className="ml-auto text-xs text-neutral-400 hover:text-neutral-700 transition-colors disabled:opacity-40"
          >
            Actualiser
          </button>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-6 py-8">
            {fetching ? (
              <div className="flex items-center justify-center py-20 gap-2 text-neutral-400">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span className="text-sm">Chargement des archives…</span>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center py-20 gap-3">
                <p className="text-sm text-red-600">{error}</p>
                <button
                  onClick={fetchArchives}
                  className="text-xs text-neutral-500 hover:text-neutral-900 underline underline-offset-2"
                >
                  Réessayer
                </button>
              </div>
            ) : archives.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
                <div className="w-16 h-16 rounded-2xl bg-neutral-100 flex items-center justify-center">
                  <svg className="w-8 h-8 text-neutral-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1 12a2 2 0 002 2h8a2 2 0 002-2L19 8" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-neutral-900">Aucun document archivé</p>
                  <p className="text-xs text-neutral-400 mt-1 max-w-xs">
                    Après avoir analysé et corrigé un contrat, envoyez{" "}
                    <span className="font-medium text-neutral-600">&ldquo;archive ce document&rdquo;</span>{" "}
                    dans le chat pour le sauvegarder ici.
                  </p>
                </div>
                <Link
                  href="/"
                  className="text-xs bg-black text-white px-4 py-2 rounded-lg hover:bg-neutral-800 transition-colors font-medium"
                >
                  Aller aux conversations
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {archives.map((item) => (
                  <ArchiveCard key={item.id} item={item} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
