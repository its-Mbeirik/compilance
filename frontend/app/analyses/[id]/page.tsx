"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

type Finding = {
  clause_id: string;
  verdict: "CONFORME" | "NON_CONFORME" | "EXIGE_REVUE";
  severity: "BLOQUANT" | "MAJEUR" | "MINEUR" | null;
  cited_article_id: string;
  quoted_text: string;
  recommendation: string | null;
  citation_valid: boolean;
};

type Analysis = {
  id: string;
  status: string;
  jurisdiction: string;
  doc_type: string;
  findings: Finding[];
  error_log: string | null;
  created_at: string | null;
  finished_at: string | null;
};

const VERDICT_STYLE: Record<string, string> = {
  CONFORME:     "bg-green-100 text-green-800",
  NON_CONFORME: "bg-red-100 text-red-800",
  EXIGE_REVUE:  "bg-yellow-100 text-yellow-800",
};
const SEVERITY_STYLE: Record<string, string> = {
  BLOQUANT: "bg-red-600 text-white",
  MAJEUR:   "bg-orange-500 text-white",
  MINEUR:   "bg-gray-400 text-white",
};

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const res = await fetch(`/api/analyses/${id}`);
        if (!res.ok) { setError("Analyse introuvable"); return; }
        const data: Analysis = await res.json();
        setAnalysis(data);
        if (data.status === "pending" || data.status === "running") {
          timer = setTimeout(poll, 2500);
        }
      } catch {
        setError("Erreur de connexion au serveur");
      }
    };

    poll();
    return () => clearTimeout(timer);
  }, [id]);

  if (error) return <p className="text-red-600 mt-12 text-center">{error}</p>;
  if (!analysis) return <p className="text-gray-400 mt-12 text-center">Chargement…</p>;

  const counts = {
    CONFORME:     analysis.findings.filter((f) => f.verdict === "CONFORME").length,
    NON_CONFORME: analysis.findings.filter((f) => f.verdict === "NON_CONFORME").length,
    EXIGE_REVUE:  analysis.findings.filter((f) => f.verdict === "EXIGE_REVUE").length,
  };

  const isPending = analysis.status === "pending" || analysis.status === "running";

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-blue-800 mb-1">Résultats d'analyse</h1>
          <p className="text-xs text-gray-400 font-mono">{analysis.id}</p>
        </div>
        {analysis.status === "done" && (
          <div className="flex gap-2">
            <a
              href={`/api/analyses/${id}/report?fmt=pdf`}
              className="bg-blue-700 text-white text-sm px-4 py-2 rounded-lg hover:bg-blue-800"
              target="_blank"
            >
              ↓ Rapport PDF
            </a>
            <Link
              href={`/analyses/${id}/chat`}
              className="border border-blue-700 text-blue-700 text-sm px-4 py-2 rounded-lg hover:bg-blue-50"
            >
              💬 Chat
            </Link>
          </div>
        )}
      </div>

      {/* Status banner */}
      {isPending && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 flex items-center gap-3">
          <span className="animate-spin text-xl">⟳</span>
          <span className="text-blue-700 text-sm">
            Analyse en cours — vérification automatique des clauses…
          </span>
        </div>
      )}
      {analysis.status === "error" && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 text-red-700 text-sm">
          <strong>Erreur :</strong> {analysis.error_log}
        </div>
      )}

      {/* Summary cards */}
      {analysis.status === "done" && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          {(["CONFORME", "NON_CONFORME", "EXIGE_REVUE"] as const).map((v) => (
            <div key={v} className="bg-white rounded-xl shadow-sm p-4 text-center">
              <p className="text-3xl font-bold text-gray-800">{counts[v]}</p>
              <span className={`text-xs px-2 py-1 rounded-full font-medium ${VERDICT_STYLE[v]}`}>{v}</span>
            </div>
          ))}
        </div>
      )}

      {/* Findings table */}
      {analysis.findings.length > 0 && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-blue-800 text-white">
              <tr>
                <th className="px-4 py-3 text-left">Clause</th>
                <th className="px-4 py-3 text-left">Verdict</th>
                <th className="px-4 py-3 text-left">Sévérité</th>
                <th className="px-4 py-3 text-left">Article</th>
                <th className="px-4 py-3 text-left">Recommandation</th>
                <th className="px-4 py-3 text-center">Cit.</th>
              </tr>
            </thead>
            <tbody>
              {analysis.findings.map((f, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 align-top">
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{f.clause_id}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${VERDICT_STYLE[f.verdict]}`}>
                      {f.verdict}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {f.severity && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${SEVERITY_STYLE[f.severity]}`}>
                        {f.severity}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-blue-700 font-mono">{f.cited_article_id}</td>
                  <td className="px-4 py-3">
                    {f.quoted_text && (
                      <p className="text-xs text-gray-500 italic border-l-2 border-gray-200 pl-2 mb-1 line-clamp-2">
                        "{f.quoted_text}"
                      </p>
                    )}
                    {f.recommendation && (
                      <p className="text-xs text-purple-700">→ {f.recommendation}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center text-sm">
                    {f.citation_valid ? "✅" : "⚠️"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-6">
        <Link href="/analyses" className="text-sm text-gray-400 hover:text-gray-600">
          ← Retour à la liste
        </Link>
      </div>
    </div>
  );
}
