"use client";

import { useEffect, useState } from "react";
import { listContracts, type Contract } from "@/lib/api";
import { IconBuilding, IconChevronRight, IconFile, IconPlus, IconUser } from "@/components/icons";

const STATUS_LABEL: Record<string, string> = {
  completed: "Analyse terminée",
  processing: "En cours",
  pending: "En attente",
  failed: "Échec",
};

export default function ContractsHistory() {
  const [contracts, setContracts] = useState<Contract[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listContracts()
      .then(setContracts)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  if (error) {
    return (
      <div className="max-w-3xl">
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>
      </div>
    );
  }
  if (!contracts) {
    return <div className="text-neutral-500 text-sm">Chargement…</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5 animate-in">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-medium text-neutral-900 tracking-tight">Historique</h1>
          <p className="text-sm text-neutral-500 mt-0.5">
            {contracts.length} contrat{contracts.length > 1 ? "s" : ""} analysé{contracts.length > 1 ? "s" : ""}
          </p>
        </div>
        <a
          href="/"
          className="inline-flex items-center gap-1.5 px-3 h-9 rounded bg-neutral-900 hover:bg-neutral-800 text-white text-sm font-medium transition-colors"
        >
          <IconPlus size={14} />
          Nouveau contrat
        </a>
      </div>

      {contracts.length === 0 ? (
        <div className="rounded border border-neutral-200 bg-white p-10 text-center">
          <div className="h-10 w-10 rounded border border-neutral-200 bg-neutral-50 flex items-center justify-center text-neutral-400 mx-auto mb-3">
            <IconFile size={18} />
          </div>
          <h2 className="font-medium text-neutral-900 mb-1 text-sm">Aucun contrat analysé</h2>
          <p className="text-xs text-neutral-500 mb-4">
            Téléversez un premier contrat pour commencer.
          </p>
          <a href="/" className="text-sm text-neutral-900 underline underline-offset-4 decoration-neutral-300 hover:decoration-neutral-900">
            Ouvrir l&apos;assistant
          </a>
        </div>
      ) : (
        <div className="rounded border border-neutral-200 bg-white divide-y divide-neutral-100 overflow-hidden">
          {contracts.map((c) => (
            <a
              key={c.id}
              href={`/reports/${c.id}`}
              className="group flex items-center gap-3 px-4 py-3 hover:bg-neutral-50 transition-colors"
            >
              <div className="h-8 w-8 rounded border border-neutral-200 bg-neutral-50 flex items-center justify-center text-neutral-600 shrink-0">
                {c.contract_type === "statuts" ? <IconBuilding size={15} /> : <IconUser size={15} />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-neutral-900 truncate">{c.filename}</div>
                <div className="text-[11px] text-neutral-500 mt-0.5 flex items-center gap-2">
                  <span>{c.contract_type === "statuts" ? "Statuts d'entreprise" : "Contrat de travail"}</span>
                  <span className="text-neutral-300">·</span>
                  <span>{new Date(c.created_at).toLocaleString("fr-FR", { dateStyle: "medium", timeStyle: "short" })}</span>
                </div>
              </div>
              <StatusPill status={c.status} />
              <IconChevronRight size={14} className="text-neutral-300 group-hover:text-neutral-600 transition-colors shrink-0" />
            </a>
          ))}
        </div>
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
    <span className="inline-flex items-center gap-1.5 text-[11px] text-neutral-600 shrink-0">
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${dot}`} />
      {STATUS_LABEL[status] || status}
    </span>
  );
}
