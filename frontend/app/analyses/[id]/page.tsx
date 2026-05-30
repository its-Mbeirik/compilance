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
  CONFORME:     "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  NON_CONFORME: "bg-red-50 text-red-700 ring-1 ring-red-200",
  EXIGE_REVUE:  "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
};
const SEVERITY_STYLE: Record<string, string> = {
  BLOQUANT: "bg-black text-white",
  MAJEUR:   "bg-neutral-600 text-white",
  MINEUR:   "bg-neutral-200 text-neutral-600",
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

  if (error) return <p className="text-red-600 mt-12 text-center text-sm">{error}</p>;
  if (!analysis) return <p className="text-neutral-400 mt-12 text-center text-sm">Chargement…</p>;

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
          <h1 className="text-xl font-semibold text-neutral-900 mb-1">
            Résultats d&apos;analyse
          </h1>
          <p className="text-xs text-neutral-400 font-mono">{analysis.id}</p>
        </div>
        {analysis.status === "done" && (
          <div className="flex gap-2">
            <a
              href={`/api/analyses/${id}/report?fmt=pdf`}
              className="bg-black text-white text-xs font-medium px-4 py-2 rounded-lg hover:bg-neutral-800 transition-colors"
              target="_blank"
            >
              ↓ Rapport PDF
            </a>
            <Link
              href="/"
              className="border border-neutral-200 text-neutral-700 text-xs font-medium px-4 py-2 rounded-lg hover:bg-neutral-50 transition-colors"
            >
              💬 Chat
            </Link>
          </div>
        )}
      </div>

      {/* Status banner */}
      {isPending && (
        <div className="bg-neutral-50 border border-neutral-200 rounded-xl p-4 mb-6 flex items-center gap-3">
          <span className="animate-spin text-lg">⟳</span>
          <span className="text-neutral-600 text-sm">
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
        <div className="grid grid-cols-3 gap-4 mb-6">
          {(["CONFORME", "NON_CONFORME", "EXIGE_REVUE"] as const).map((v) => (
            <div key={v} className="bg-white rounded-xl border border-neutral-100 p-4 text-center">
              <p className="text-3xl font-bold text-neutral-900">{counts[v]}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${VERDICT_STYLE[v]}`}>
                {v.replace("_", " ")}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Findings table */}
      {analysis.findings.length > 0 && (
        <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden">
          <table className="w-full text-xs">
            <thead className="bg-neutral-900 text-white">
              <tr>
                <th className="px-3 py-2.5 text-left font-medium tracking-wide">Clause</th>
                <th className="px-3 py-2.5 text-left font-medium tracking-wide">Verdict</th>
                <th className="px-3 py-2.5 text-left font-medium tracking-wide">Sévérité</th>
                <th className="px-3 py-2.5 text-left font-medium tracking-wide">Article</th>
                <th className="px-3 py-2.5 text-left font-medium tracking-wide">Recommandation</th>
                <th className="px-3 py-2.5 text-center font-medium tracking-wide">Cit.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {analysis.findings.map((f, i) => (
                <tr key={i} className="hover:bg-neutral-50 align-top transition-colors">
                  <td className="px-3 py-2.5 font-mono text-neutral-400 whitespace-nowrap">{f.clause_id}</td>
                  <td className="px-3 py-2.5 whitespace-nowrap">
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${VERDICT_STYLE[f.verdict]}`}>
                      {f.verdict}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 whitespace-nowrap">
                    {f.severity && (
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${SEVERITY_STYLE[f.severity]}`}>
                        {f.severity}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 font-mono text-neutral-700 whitespace-nowrap font-semibold">
                    {f.cited_article_id}
                  </td>
                  <td className="px-3 py-2.5 max-w-xs">
                    {f.quoted_text && (
                      <p className="text-neutral-500 italic border-l-2 border-neutral-200 pl-2 mb-1 line-clamp-2">
                        &ldquo;{f.quoted_text}&rdquo;
                      </p>
                    )}
                    {f.recommendation && (
                      <p className="text-violet-600">→ {f.recommendation}</p>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-center">
                    {f.citation_valid ? "✅" : "⚠️"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-6">
        <Link href="/analyses" className="text-xs text-neutral-400 hover:text-neutral-700 transition-colors">
          ← Retour à la liste
        </Link>
      </div>
    </div>
  );
}
