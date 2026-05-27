"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  downloadReportUrl,
  generateCorrected,
  getContract,
  triggerBrowserDownload,
  type Contract,
  type Finding,
} from "@/lib/api";
import { IconCheck, IconChevronRight, IconDownload, IconLoader, IconSparkles } from "@/components/icons";

const SEVERITY_ORDER: Record<Finding["severity"], number> = {
  CRITIQUE: 0,
  MAJEURE: 1,
  MINEURE: 2,
};

const STATUS_LABEL: Record<string, string> = {
  completed: "Analyse terminée",
  processing: "Analyse en cours",
  pending: "En file d'attente",
  failed: "Échec de l'analyse",
};

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const [contract, setContract] = useState<Contract | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  async function handleGenerateCorrected() {
    if (!contract) return;
    setGenError(null);
    setGenerating(true);
    try {
      const blob = await generateCorrected(contract.id, "docx");
      const base = contract.filename.replace(/\.[^.]+$/, "");
      triggerBrowserDownload(blob, `contrat_corrige_${base}.docx`);
    } catch (e) {
      setGenError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    let interval: ReturnType<typeof setInterval> | undefined;

    async function poll() {
      try {
        const c = await getContract(params.id);
        if (cancelled) return;
        setContract(c);
        if (c.status === "completed" || c.status === "failed") {
          if (interval) clearInterval(interval);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }

    poll();
    interval = setInterval(poll, 3000);
    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
  }, [params.id]);

  if (error) return <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>;
  if (!contract) return <div className="text-neutral-500 text-sm">Chargement…</div>;

  const sorted = [...contract.findings].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9),
  );
  const counts = sorted.reduce(
    (acc, f) => ((acc[f.severity] = (acc[f.severity] || 0) + 1), acc),
    {} as Record<string, number>,
  );

  return (
    <div className="max-w-4xl mx-auto space-y-5 animate-in">
      <nav className="flex items-center gap-1 text-xs text-neutral-500">
        <a href="/contracts" className="hover:text-neutral-900">Historique</a>
        <IconChevronRight size={12} className="text-neutral-400" />
        <span className="text-neutral-700 truncate">Rapport</span>
      </nav>

      <header className="border-b border-neutral-200 pb-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="min-w-0">
            <h1 className="text-xl font-medium text-neutral-900 truncate tracking-tight">{contract.filename}</h1>
            <div className="flex items-center gap-2 mt-1 text-xs text-neutral-500">
              <span>{contract.contract_type === "statuts" ? "Statuts d'entreprise" : "Contrat de travail"}</span>
              <span className="text-neutral-300">·</span>
              <span>{new Date(contract.created_at).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" })}</span>
            </div>
          </div>
          <StatusPill status={contract.status} />
        </div>

        {contract.status === "completed" && (
          <>
            <div className="grid grid-cols-3 gap-3 mt-5">
              <StatCard label="Critiques" value={counts.CRITIQUE || 0} color="red" />
              <StatCard label="Majeures" value={counts.MAJEURE || 0} color="orange" />
              <StatCard label="Mineures" value={counts.MINEURE || 0} color="amber" />
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-1.5">
              <a
                href={downloadReportUrl(contract.id, "docx")}
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded border border-neutral-200 bg-white hover:bg-neutral-50 text-xs text-neutral-700 transition-colors"
              >
                <IconDownload size={13} />
                Télécharger le rapport (.docx)
              </a>
              <a
                href={downloadReportUrl(contract.id, "md")}
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded border border-neutral-200 bg-white hover:bg-neutral-50 text-xs text-neutral-700 transition-colors"
              >
                <IconDownload size={13} />
                Markdown
              </a>
              <button
                onClick={handleGenerateCorrected}
                disabled={generating || (contract.findings?.length ?? 0) === 0}
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded bg-neutral-900 hover:bg-neutral-800 text-xs text-white transition-colors disabled:opacity-50"
                title={(contract.findings?.length ?? 0) === 0 ? "Aucune non-conformité à corriger" : ""}
              >
                {generating ? <IconLoader size={13} /> : <IconSparkles size={13} />}
                {generating ? "Génération en cours…" : "Générer la version corrigée (.docx)"}
              </button>
              {genError && <span className="text-xs text-red-700 ml-1">{genError}</span>}
            </div>
          </>
        )}
      </header>

      {contract.status === "processing" && (
        <div className="rounded border border-amber-200 bg-amber-50 px-3 py-2.5 text-amber-800 text-sm flex items-center gap-2 animate-in">
          <IconLoader size={14} />
          Analyse en cours, cette page se met à jour automatiquement.
        </div>
      )}

      {contract.status === "completed" && (
        <>
          <section>
            <h2 className="text-sm font-medium text-neutral-900 mb-3 uppercase tracking-wider">
              Non-conformités détaillées
            </h2>
            {sorted.length === 0 ? (
              <div className="rounded border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 flex items-center gap-3">
                <span className="h-7 w-7 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                  <IconCheck size={14} />
                </span>
                <div className="text-sm">
                  <div className="font-medium">Aucune non-conformité détectée.</div>
                  <div className="text-xs opacity-80 mt-0.5">Le document semble conforme aux dispositions légales examinées.</div>
                </div>
              </div>
            ) : (
              <ol className="space-y-2.5">
                {sorted.map((f, i) => (
                  <li key={f.id} className="rounded border border-neutral-200 bg-white p-4 animate-in">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span className="text-xs text-neutral-400 font-mono shrink-0 tabular-nums">{String(i + 1).padStart(2, "0")}</span>
                        <span className="font-medium text-neutral-900 truncate">
                          {f.clause_ref || "Clause manquante"}
                        </span>
                        <span className="text-xs text-neutral-400 hidden sm:inline">· {f.category}</span>
                      </div>
                      <SeverityBadge severity={f.severity} />
                    </div>
                    <p className="text-sm text-neutral-700 leading-relaxed">{f.description}</p>
                    {f.recommendation && (
                      <div className="mt-3 pt-3 border-t border-neutral-100">
                        <div className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider mb-1">Recommandation</div>
                        <p className="text-sm text-neutral-700 leading-relaxed">{f.recommendation}</p>
                      </div>
                    )}
                    {f.legal_basis && f.legal_basis.length > 0 && (
                      <details className="mt-3 pt-3 border-t border-neutral-100 text-xs group">
                        <summary className="cursor-pointer text-neutral-500 hover:text-neutral-800 font-medium inline-flex items-center gap-1">
                          Base légale ({f.legal_basis.length})
                          <span className="transition-transform group-open:rotate-90"><IconChevronRight size={11} /></span>
                        </summary>
                        <ul className="mt-2 space-y-1.5">
                          {f.legal_basis.map((lb, j) => (
                            <li key={j} className="text-neutral-600 leading-relaxed">
                              <span className="font-medium text-neutral-700">{lb.source}</span>
                              {lb.article && <span className="text-neutral-500"> — {lb.article}</span>}
                              <div className="italic opacity-80 mt-0.5">
                                « {lb.excerpt.slice(0, 250)}{lb.excerpt.length > 250 ? "…" : ""} »
                              </div>
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                    <div className="mt-2 text-[11px] text-neutral-400 tabular-nums">
                      Confiance · {(f.confidence * 100).toFixed(0)}%
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>

          {contract.report && (
            <section>
              <h2 className="text-sm font-medium text-neutral-900 mb-3 uppercase tracking-wider">Rapport synthétique</h2>
              <article className="rounded border border-neutral-200 bg-white p-5 prose prose-sm prose-neutral max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{contract.report}</ReactMarkdown>
              </article>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const dot =
    status === "completed" ? "bg-emerald-500"
    : status === "processing" || status === "pending" ? "bg-amber-500"
    : status === "failed" ? "bg-red-500"
    : "bg-neutral-300";
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-neutral-600 shrink-0">
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${dot}`} />
      {STATUS_LABEL[status] || status}
    </span>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: "red" | "orange" | "amber" }) {
  const accent =
    color === "red" ? "border-red-200 text-red-700"
    : color === "orange" ? "border-orange-200 text-orange-700"
    : "border-amber-200 text-amber-700";
  return (
    <div className={`rounded border ${accent} bg-white p-4`}>
      <div className="text-2xl font-medium tabular-nums">{value}</div>
      <div className="text-[11px] uppercase tracking-wider font-medium mt-1 opacity-80">{label}</div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const cls = severity === "CRITIQUE" ? "text-red-700 border-red-200"
    : severity === "MAJEURE" ? "text-orange-700 border-orange-200"
    : "text-amber-700 border-amber-200";
  return (
    <span className={`text-[10px] uppercase tracking-wider font-medium px-1.5 py-0.5 rounded border shrink-0 ${cls}`}>
      {severity}
    </span>
  );
}
