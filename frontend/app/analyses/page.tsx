"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

type AnalysisSummary = {
  id: string;
  analysis_id: string;
  status: string;
  jurisdiction: string;
  doc_type: string;
  created_at: string | null;
};

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-neutral-100 text-neutral-600",
  running: "bg-amber-50 text-amber-700",
  done:    "bg-emerald-50 text-emerald-700",
  error:   "bg-red-50 text-red-700",
};

export default function AnalysesPage() {
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/analyses")
      .then((r) => r.json())
      .then((data) => { setAnalyses(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-neutral-400 mt-12 text-center text-sm">Chargement…</p>;

  if (!analyses.length)
    return (
      <div className="text-center mt-16">
        <p className="text-neutral-500 mb-4 text-sm">Aucune analyse pour le moment.</p>
        <Link href="/" className="text-sm font-medium text-neutral-900 underline underline-offset-2">
          Lancer une analyse →
        </Link>
      </div>
    );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-neutral-900">Analyses</h1>
        <Link
          href="/"
          className="bg-black text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-neutral-800 transition-colors"
        >
          + Nouvelle analyse
        </Link>
      </div>
      <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-neutral-900 text-white">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-xs tracking-wide">ID</th>
              <th className="px-4 py-3 text-left font-medium text-xs tracking-wide">Type</th>
              <th className="px-4 py-3 text-left font-medium text-xs tracking-wide">Statut</th>
              <th className="px-4 py-3 text-left font-medium text-xs tracking-wide">Date</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {analyses.map((a) => (
              <tr key={a.id} className="hover:bg-neutral-50 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-neutral-400">{a.id.slice(0, 8)}…</td>
                <td className="px-4 py-3 text-neutral-700">
                  {a.doc_type === "contrat_travail" ? "Contrat de travail" : a.doc_type}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_STYLE[a.status] ?? "bg-neutral-100 text-neutral-600"}`}>
                    {a.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-neutral-400">
                  {a.created_at ? new Date(a.created_at).toLocaleString("fr-FR") : "—"}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/analyses/${a.id}`}
                    className="text-xs font-medium text-neutral-900 hover:underline underline-offset-2"
                  >
                    Voir →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
