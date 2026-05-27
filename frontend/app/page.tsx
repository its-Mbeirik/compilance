"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  downloadReportUrl,
  generateCorrected,
  getContract,
  listContracts,
  sendChat,
  triggerBrowserDownload,
  uploadContract,
  type ChatMessage,
  type ChatSource,
  type Contract,
  type Finding,
} from "@/lib/api";
import {
  IconArrowUp,
  IconBook,
  IconClose,
  IconDownload,
  IconFile,
  IconLoader,
  IconPaperclip,
  IconPlus,
  IconScale,
  IconSparkles,
  IconUser,
} from "@/components/icons";

type Turn = {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  contractId?: string;
  findings?: Finding[];
  uploadName?: string;
};

const SUGGESTED_PROMPTS = [
  "Quelle est la durée légale du travail hebdomadaire ?",
  "Capital social minimum pour constituer une SARL ?",
  "Règles encadrant le travail des mineurs",
  "Période d'essai d'un contrat à durée indéterminée",
];

export default function ChatHome() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [contractId, setContractId] = useState<string>("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [contractType, setContractType] = useState("statuts");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    refreshContracts();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns, loading, uploading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  async function refreshContracts() {
    try {
      setContracts(await listContracts());
    } catch {
      /* ignore */
    }
  }

  async function pollUntilDone(id: string) {
    let attempts = 0;
    while (attempts < 200) {
      try {
        const c = await getContract(id);
        if (c.status === "completed" || c.status === "failed") return c;
      } catch {
        /* ignore */
      }
      await new Promise((r) => setTimeout(r, 3000));
      attempts++;
    }
    return null;
  }

  function detectContractType(name: string): "statuts" | "contrat_travail" {
    const n = name.toLowerCase();
    if (/(travail|emploi|salari|cdi|cdd|employee)/.test(n)) return "contrat_travail";
    if (/(statut|soci[ée]t[ée]|sarl|sa[\s_-]|sas)/.test(n)) return "statuts";
    return contractType as "statuts" | "contrat_travail";
  }

  async function handleFile(file: File) {
    setError(null);
    setUploading(true);

    const detected = detectContractType(file.name);
    setContractType(detected);
    const typeLabel = detected === "statuts" ? "Statuts d'entreprise" : "Contrat de travail";
    setTurns((prev) => [
      ...prev,
      { role: "user", content: typeLabel, uploadName: file.name },
      {
        role: "assistant",
        content: "Document reçu. **Analyse en cours.** _L'opération prend généralement entre 30 et 90 secondes selon la longueur du contrat._",
      },
    ]);

    try {
      const c = await uploadContract(file, detected);
      setContractId(c.id);
      refreshContracts();

      const final = await pollUntilDone(c.id);

      if (!final) {
        setTurns((prev) => [
          ...prev,
          { role: "assistant", content: "Délai d'analyse dépassé. Vous pouvez consulter le statut depuis l'historique." },
        ]);
        return;
      }

      if (final.status === "failed") {
        setTurns((prev) => [
          ...prev,
          { role: "assistant", content: "L'analyse a échoué. Vérifiez que le document est lisible et réessayez." },
        ]);
        return;
      }

      const findings = final.findings || [];
      const summary = findings.length === 0
        ? `## ${final.filename}\n\n**Aucune non-conformité détectée.** Le document semble conforme aux dispositions légales examinées.`
        : `## Analyse de **${final.filename}**\n\nLe contrat est désormais sélectionné comme contexte actif. Vous pouvez poser des questions de suivi sur ses clauses, ou consulter le [rapport détaillé](/reports/${final.id}).`;

      setTurns((prev) => [
        ...prev,
        { role: "assistant", content: summary, contractId: final.id, findings },
      ]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      setTurns((prev) => [...prev, { role: "assistant", content: `Erreur : ${msg}` }]);
    } finally {
      setUploading(false);
    }
  }

  async function handleSend(e?: React.FormEvent) {
    e?.preventDefault();
    const q = input.trim();
    if (!q || loading) return;
    setError(null);

    const newTurns: Turn[] = [...turns, { role: "user", content: q }];
    setTurns(newTurns);
    setInput("");
    setLoading(true);

    try {
      const history: ChatMessage[] = newTurns
        .filter((t) => !t.uploadName)
        .map((t) => ({ role: t.role, content: t.content }));
      const res = await sendChat(history, { contractId: contractId || null, k: 5 });
      setTurns([...newTurns, { role: "assistant", content: res.reply, sources: res.sources }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function quickPrompt(p: string) {
    setInput(p);
    setTimeout(() => textareaRef.current?.focus(), 50);
  }

  const selectedContract = contracts.find((c) => c.id === contractId);
  const isEmpty = turns.length === 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-5 h-[calc(100vh-6rem)]">
      {/* Sidebar */}
      <aside className="hidden lg:flex flex-col gap-3 overflow-hidden">
        <button
          onClick={() => { setTurns([]); setContractId(""); }}
          className="flex items-center gap-2 px-3 h-9 rounded border border-neutral-200 bg-white hover:bg-neutral-100 text-neutral-800 text-sm font-medium transition-colors"
        >
          <IconPlus size={14} />
          Nouvelle conversation
        </button>

        <div className="rounded border border-neutral-200 bg-white flex-1 overflow-hidden flex flex-col">
          <div className="text-[11px] font-medium text-neutral-500 uppercase tracking-wider px-3 py-2.5 border-b border-neutral-100">
            Contrats récents
          </div>
          <div className="flex-1 overflow-y-auto py-1">
            {contracts.length === 0 ? (
              <div className="text-xs text-neutral-400 px-3 py-2">Aucun contrat analysé.</div>
            ) : (
              <ul>
                {contracts.slice(0, 20).map((c) => (
                  <li key={c.id}>
                    <button
                      onClick={() => setContractId(c.id)}
                      className={`w-full text-left px-3 py-2 text-xs transition-colors border-l-2 ${
                        contractId === c.id
                          ? "border-neutral-900 bg-neutral-50 text-neutral-900"
                          : "border-transparent text-neutral-700 hover:bg-neutral-50"
                      }`}
                    >
                      <div className="font-medium truncate">{c.filename}</div>
                      <div className="flex items-center gap-1.5 mt-1 text-neutral-400">
                        <StatusDot status={c.status} />
                        <span>{c.contract_type === "statuts" ? "Statuts" : "Contrat travail"}</span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex flex-col min-h-0">
        {selectedContract && (
          <div className="mb-3 rounded border border-neutral-200 bg-white px-3.5 py-2.5 flex items-center justify-between text-sm animate-in">
            <div className="flex items-center gap-2 min-w-0 text-neutral-700">
              <IconFile size={14} className="text-neutral-400 shrink-0" />
              <span className="truncate font-medium">{selectedContract.filename}</span>
              <span className="text-neutral-400 text-xs hidden sm:inline">· contexte actif</span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              {selectedContract.status === "completed" && (
                <a
                  href={`/reports/${selectedContract.id}`}
                  className="text-xs px-2 h-7 inline-flex items-center rounded border border-neutral-200 hover:bg-neutral-100 text-neutral-700 transition-colors"
                >
                  Rapport
                </a>
              )}
              <button
                onClick={() => setContractId("")}
                className="h-7 w-7 inline-flex items-center justify-center rounded text-neutral-400 hover:text-neutral-700 hover:bg-neutral-100 transition-colors"
                title="Retirer le contexte"
              >
                <IconClose size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Message list */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto rounded border border-neutral-200 bg-white p-6 min-h-0"
        >
          {isEmpty ? (
            <EmptyState onPick={quickPrompt} />
          ) : (
            <div className="space-y-5 max-w-3xl mx-auto">
              {turns.map((t, i) => (
                <Bubble key={i} turn={t} />
              ))}
              {(loading || uploading) && <TypingIndicator label={uploading ? "Analyse du contrat" : null} />}
            </div>
          )}

          {error && (
            <div className="mt-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 animate-in">
              {error}
            </div>
          )}
        </div>

        {/* Composer */}
        <form
          onSubmit={handleSend}
          className="mt-3 rounded border border-neutral-300 bg-white px-2 py-2 focus-within:border-neutral-500 transition-colors"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
              if (fileInputRef.current) fileInputRef.current.value = "";
            }}
          />
          <div className="flex items-end gap-1.5">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading || loading}
              title="Téléverser un contrat (type détecté automatiquement)"
              className="flex items-center justify-center h-9 w-9 rounded text-neutral-500 hover:bg-neutral-100 hover:text-neutral-800 transition-colors disabled:opacity-40"
            >
              <IconPaperclip size={17} />
            </button>

            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={selectedContract
                ? `Posez une question sur ${selectedContract.filename}...`
                : "Posez une question juridique, ou joignez un contrat à analyser..."}
              disabled={loading || uploading}
              rows={1}
              className="flex-1 bg-transparent px-2 py-2 resize-none outline-none placeholder:text-neutral-400 text-[14px] leading-6 text-neutral-900"
            />

            <button
              type="submit"
              disabled={!input.trim() || loading || uploading}
              className="flex items-center justify-center h-9 w-9 rounded bg-neutral-900 hover:bg-neutral-800 text-white disabled:bg-neutral-300 disabled:cursor-not-allowed transition-colors"
              title="Envoyer (Entrée)"
            >
              <IconArrowUp size={15} />
            </button>
          </div>
          <div className="text-[11px] text-neutral-400 px-1.5 mt-1">
            Entrée pour envoyer · Shift+Entrée pour saut de ligne
          </div>
        </form>
      </div>
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (s: string) => void }) {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-6 py-8 max-w-2xl mx-auto">
      <div className="h-10 w-10 rounded border border-neutral-200 bg-neutral-50 flex items-center justify-center text-neutral-700 mb-5">
        <IconScale size={20} />
      </div>
      <h2 className="text-xl font-medium text-neutral-900 mb-2 tracking-tight">
        Assistant juridique
      </h2>
      <p className="text-neutral-500 max-w-lg mb-8 text-[14px] leading-relaxed">
        Posez une question relative au droit mauritanien, ou joignez un contrat
        (statuts d&apos;entreprise, contrat de travail) pour le vérifier contre
        le corpus légal indexé.
      </p>

      <div className="w-full max-w-xl">
        <div className="text-[11px] font-medium text-neutral-400 uppercase tracking-wider mb-2 text-left">
          Exemples
        </div>
        <div className="flex flex-col gap-1.5">
          {SUGGESTED_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => onPick(p)}
              className="text-left rounded border border-neutral-200 bg-white hover:bg-neutral-50 hover:border-neutral-300 px-3.5 py-2.5 text-sm text-neutral-700 transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function TypingIndicator({ label }: { label?: string | null }) {
  return (
    <div className="flex items-start gap-3 animate-in">
      <div className="h-7 w-7 rounded border border-neutral-200 bg-neutral-50 flex items-center justify-center text-neutral-600 shrink-0">
        <IconScale size={13} />
      </div>
      <div className="flex items-center gap-2 px-3 py-2 text-neutral-500 text-sm">
        <span>
          <span className="typing-dot"></span>
          <span className="typing-dot"></span>
          <span className="typing-dot"></span>
        </span>
        {label && <span className="text-xs">{label}</span>}
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "completed" ? "bg-emerald-500"
    : status === "processing" || status === "pending" ? "bg-amber-500"
    : status === "failed" ? "bg-red-500"
    : "bg-neutral-300";
  return <span className={`inline-block h-1.5 w-1.5 rounded-full ${color}`} />;
}

function Bubble({ turn }: { turn: Turn }) {
  const isUser = turn.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end animate-in">
        <div className="max-w-[85%] flex items-start gap-3">
          <div className="flex-1">
            {turn.uploadName ? (
              <div className="rounded border border-neutral-300 bg-neutral-50 px-3.5 py-2.5">
                <div className="flex items-center gap-2.5">
                  <span className="h-8 w-8 rounded border border-neutral-200 bg-white flex items-center justify-center text-neutral-600 shrink-0">
                    <IconFile size={15} />
                  </span>
                  <div className="min-w-0">
                    <div className="font-medium text-neutral-900 text-sm truncate">{turn.uploadName}</div>
                    <div className="text-[11px] text-neutral-500">{turn.content}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded border border-neutral-300 bg-neutral-50 px-3.5 py-2.5 text-[14px] text-neutral-900 leading-relaxed whitespace-pre-wrap">
                {turn.content}
              </div>
            )}
          </div>
          <div className="h-7 w-7 rounded border border-neutral-200 bg-white flex items-center justify-center text-neutral-500 shrink-0">
            <IconUser size={13} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start animate-in">
      <div className="max-w-[90%] flex items-start gap-3 w-full">
        <div className="h-7 w-7 rounded border border-neutral-200 bg-neutral-50 flex items-center justify-center text-neutral-700 shrink-0">
          <IconScale size={13} />
        </div>
        <div className="flex-1 min-w-0 pt-0.5">
          <div className="prose prose-sm prose-neutral max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{turn.content}</ReactMarkdown>
          </div>

          {turn.contractId && (
            <ContractActions contractId={turn.contractId} filename={turn.uploadName} />
          )}

          {turn.findings && turn.findings.length > 0 && (
            <FindingsBlock findings={turn.findings} />
          )}

          {turn.sources && turn.sources.length > 0 && (
            <SourcesBlock sources={turn.sources} />
          )}
        </div>
      </div>
    </div>
  );
}

function ContractActions({ contractId, filename }: { contractId: string; filename?: string }) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCorrected() {
    setError(null);
    setGenerating(true);
    try {
      const blob = await generateCorrected(contractId, "docx");
      const base = (filename || "contrat").replace(/\.[^.]+$/, "");
      triggerBrowserDownload(blob, `contrat_corrige_${base}.docx`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-1.5">
      <a
        href={downloadReportUrl(contractId, "docx")}
        className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded border border-neutral-200 bg-white hover:bg-neutral-50 text-xs text-neutral-700 transition-colors"
      >
        <IconDownload size={12} />
        Rapport (.docx)
      </a>
      <a
        href={downloadReportUrl(contractId, "md")}
        className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded border border-neutral-200 bg-white hover:bg-neutral-50 text-xs text-neutral-700 transition-colors"
      >
        <IconDownload size={12} />
        Rapport (.md)
      </a>
      <button
        onClick={handleCorrected}
        disabled={generating}
        className="inline-flex items-center gap-1.5 h-7 px-2.5 rounded border border-neutral-300 bg-neutral-900 hover:bg-neutral-800 text-xs text-white transition-colors disabled:opacity-50"
      >
        {generating ? <IconLoader size={12} /> : <IconSparkles size={12} />}
        {generating ? "Génération…" : "Générer contrat corrigé (.docx)"}
      </button>
      {error && (
        <span className="text-xs text-red-700 ml-1">{error}</span>
      )}
    </div>
  );
}

function FindingsBlock({ findings }: { findings: Finding[] }) {
  const counts = findings.reduce(
    (acc, f) => ((acc[f.severity] = (acc[f.severity] || 0) + 1), acc),
    {} as Record<string, number>,
  );

  return (
    <div className="mt-3">
      <div className="flex flex-wrap gap-1.5 mb-2">
        {counts.CRITIQUE > 0 && <SeverityChip severity="CRITIQUE" count={counts.CRITIQUE} />}
        {counts.MAJEURE > 0 && <SeverityChip severity="MAJEURE" count={counts.MAJEURE} />}
        {counts.MINEURE > 0 && <SeverityChip severity="MINEURE" count={counts.MINEURE} />}
      </div>
      <details className="text-sm group">
        <summary className="cursor-pointer text-neutral-600 hover:text-neutral-900 text-xs font-medium select-none inline-flex items-center gap-1">
          Voir les {findings.length} non-conformité{findings.length > 1 ? "s" : ""}
          <span className="transition-transform group-open:rotate-90"><IconChev /></span>
        </summary>
        <ul className="mt-3 space-y-2">
          {findings
            .sort((a, b) => {
              const order: Record<string, number> = { CRITIQUE: 0, MAJEURE: 1, MINEURE: 2 };
              return (order[a.severity] ?? 9) - (order[b.severity] ?? 9);
            })
            .map((f) => (
              <li key={f.id} className="rounded border border-neutral-200 bg-white px-3 py-2.5 text-sm">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-medium text-neutral-900">
                    {f.clause_ref || "Clause manquante"}
                  </span>
                  <SeverityBadge severity={f.severity} />
                </div>
                <div className="text-neutral-700 leading-relaxed">{f.description}</div>
                {f.recommendation && (
                  <div className="text-neutral-500 mt-1.5 text-[13px]">
                    <span className="text-neutral-400">Recommandation — </span>
                    {f.recommendation}
                  </div>
                )}
              </li>
            ))}
        </ul>
      </details>
    </div>
  );
}

function SourcesBlock({ sources }: { sources: ChatSource[] }) {
  return (
    <details className="mt-3 text-sm group">
      <summary className="cursor-pointer text-neutral-500 hover:text-neutral-800 text-xs font-medium select-none inline-flex items-center gap-1.5">
        <IconBook size={12} />
        {sources.length} source{sources.length > 1 ? "s" : ""} consultée{sources.length > 1 ? "s" : ""}
        <span className="transition-transform group-open:rotate-90"><IconChev /></span>
      </summary>
      <ul className="mt-2.5 space-y-1.5">
        {sources.map((s, i) => (
          <li key={i} className="rounded border border-neutral-200 bg-neutral-50 px-3 py-2 text-xs">
            <div className="flex items-center justify-between gap-2 mb-0.5">
              <span className="font-medium text-neutral-800 truncate">
                {s.source}{s.article ? ` — ${s.article}` : ""}
              </span>
              <span className="text-neutral-400 shrink-0 tabular-nums">{s.score.toFixed(2)}</span>
            </div>
            <div className="text-neutral-600 italic leading-relaxed">
              « {s.excerpt.slice(0, 260)}{s.excerpt.length > 260 ? "…" : ""} »
            </div>
          </li>
        ))}
      </ul>
    </details>
  );
}

function SeverityChip({ severity, count }: { severity: string; count: number }) {
  const cls = severity === "CRITIQUE" ? "bg-red-50 text-red-700 border-red-200"
    : severity === "MAJEURE" ? "bg-orange-50 text-orange-700 border-orange-200"
    : "bg-amber-50 text-amber-700 border-amber-200";
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border ${cls}`}>
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${severity === "CRITIQUE" ? "bg-red-500" : severity === "MAJEURE" ? "bg-orange-500" : "bg-amber-500"}`} />
      {count} {severity.toLowerCase()}{count > 1 ? "s" : ""}
    </span>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const cls = severity === "CRITIQUE" ? "text-red-700 border-red-200"
    : severity === "MAJEURE" ? "text-orange-700 border-orange-200"
    : "text-amber-700 border-amber-200";
  return (
    <span className={`text-[10px] uppercase tracking-wide font-medium px-1.5 py-0.5 rounded border ${cls}`}>
      {severity}
    </span>
  );
}

function IconChev() {
  return (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m9 18 6-6-6-6"/>
    </svg>
  );
}
