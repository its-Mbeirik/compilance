"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

type AnalysisSummary = {
  id: string;
  status: string;
  jurisdiction: string;
  doc_type: string;
  created_at: string | null;
};

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  running: "bg-blue-100 text-blue-800",
  done: "bg-green-100 text-green-800",
  error: "bg-red-100 text-red-800",
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

  if (loading) return <p className="text-gray-400 mt-12 text-center">Chargement…</p>;

  if (!analyses.length)
    return (
      <div className="text-center mt-16">
        <p className="text-gray-500 mb-4">Aucune analyse pour le moment.</p>
        <Link href="/upload" className="text-blue-700 underline">Lancer une analyse →</Link>
      </div>
    );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-blue-800">Mes analyses</h1>
        <Link href="/upload" className="bg-blue-700 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-800">
          + Nouvelle analyse
        </Link>
      </div>
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-blue-800 text-white">
            <tr>
              <th className="px-4 py-3 text-left">ID</th>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Juridiction</th>
              <th className="px-4 py-3 text-left">Statut</th>
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {analyses.map((a) => (
              <tr key={a.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{a.id.slice(0, 8)}…</td>
                <td className="px-4 py-3">{a.doc_type}</td>
                <td className="px-4 py-3 text-xs">{a.jurisdiction}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_STYLE[a.status] ?? ""}`}>
                    {a.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-gray-400">
                  {a.created_at ? new Date(a.created_at).toLocaleString("fr-FR") : "—"}
                </td>
                <td className="px-4 py-3">
                  <Link href={`/analyses/${a.id}`} className="text-blue-600 hover:underline text-xs">
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
