"use client";
import { useState, useRef, useEffect, useCallback } from "react";

// ── Types ──────────────────────────────────────────────────────────────────

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
  created_at?: string;
};

type HistoryItem = {
  analysis_id: string;
  status: string;
  doc_type: string;
  created_at: string;
};

type Msg =
  | { kind: "user";     text: string }
  | { kind: "bot";      text: string }
  | { kind: "thinking" }
  | { kind: "result";   analysis: Analysis }
  | { kind: "document"; filename: string; blobUrl: string }
  | { kind: "error";    text: string };

// ── Verdict / severity styles ──────────────────────────────────────────────

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

// ── Findings card ──────────────────────────────────────────────────────────

function FindingsCard({ analysis }: { analysis: Analysis }) {
  const counts = {
    CONFORME:     analysis.findings.filter((f) => f.verdict === "CONFORME").length,
    NON_CONFORME: analysis.findings.filter((f) => f.verdict === "NON_CONFORME").length,
    EXIGE_REVUE:  analysis.findings.filter((f) => f.verdict === "EXIGE_REVUE").length,
  };
  const total = analysis.findings.length;

  return (
    <div className="w-full">
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <span className="text-xs font-semibold text-neutral-400 uppercase tracking-widest">
          Droit mauritanien
        </span>
        <span className="text-neutral-300">·</span>
        <span className="text-sm font-semibold text-neutral-900">{total} clause{total !== 1 ? "s" : ""}</span>
        <div className="flex gap-1.5 ml-1 flex-wrap">
          {(["NON_CONFORME", "EXIGE_REVUE", "CONFORME"] as const).map((v) =>
            counts[v] > 0 ? (
              <span key={v} className={`text-xs px-2 py-0.5 rounded-full font-medium ${VERDICT_STYLE[v]}`}>
                {counts[v]} {v.replace("_", " ")}
              </span>
            ) : null
          )}
        </div>
        <a
          href={`/api/analyses/${analysis.id}/report?fmt=pdf`}
          target="_blank"
          className="ml-auto text-xs text-neutral-500 hover:text-neutral-900 font-medium flex items-center gap-1 shrink-0 underline underline-offset-2"
        >
          Rapport PDF
        </a>
      </div>

      {analysis.findings.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-neutral-200">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-neutral-50 text-neutral-500 font-medium border-b border-neutral-200">
                <th className="px-3 py-2 text-left">Clause</th>
                <th className="px-3 py-2 text-left">Verdict</th>
                <th className="px-3 py-2 text-left">Sévérité</th>
                <th className="px-3 py-2 text-left">Article</th>
                <th className="px-3 py-2 text-left">Recommandation</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-neutral-100">
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
                  <td className="px-3 py-2.5 font-mono text-neutral-700 whitespace-nowrap font-semibold">{f.cited_article_id}</td>
                  <td className="px-3 py-2.5 text-neutral-600 max-w-xs">
                    {f.recommendation ?? <span className="text-neutral-300">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-sm text-neutral-400 italic">Aucune clause détectée.</p>
      )}
    </div>
  );
}

// ── Document download card ─────────────────────────────────────────────────

function DocumentCard({ filename, blobUrl }: { filename: string; blobUrl: string }) {
  return (
    <div className="flex items-center gap-3 bg-neutral-50 border border-neutral-200 rounded-xl px-4 py-3">
      <div className="w-9 h-9 rounded-lg bg-black flex items-center justify-center shrink-0">
        <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-neutral-900 truncate">{filename}</p>
        <p className="text-xs text-neutral-400 mt-0.5">Document Word · prêt à télécharger</p>
      </div>
      <a
        href={blobUrl}
        download={filename}
        className="flex items-center gap-1.5 bg-black text-white text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-neutral-800 transition-colors shrink-0"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Télécharger
      </a>
    </div>
  );
}

// ── Small atoms ────────────────────────────────────────────────────────────

function BotAvatar() {
  return (
    <div className="w-7 h-7 rounded-full bg-black flex items-center justify-center shrink-0 text-white text-xs font-bold">
      ⚖
    </div>
  );
}

function ThinkingDots() {
  return (
    <div className="flex gap-1 items-center py-0.5">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-neutral-400 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "done"    ? "bg-emerald-400" :
    status === "error"   ? "bg-red-400"     :
    status === "running" ? "bg-amber-400"   :
                           "bg-neutral-400";
  return <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${color}`} />;
}

// ── Sidebar ────────────────────────────────────────────────────────────────

function Sidebar({
  history,
  activeId,
  onSelect,
  onNew,
  open,
  onClose,
}: {
  history: HistoryItem[];
  activeId: string | null;
  onSelect: (item: HistoryItem) => void;
  onNew: () => void;
  open: boolean;
  onClose: () => void;
}) {
  const fmt = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
    } catch { return ""; }
  };

  const label = (item: HistoryItem) =>
    item.doc_type === "contrat_travail" ? "Contrat de travail" :
    item.doc_type === "statuts"         ? "Statuts"            :
                                          "Analyse";

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-30
          w-64 bg-[#111] flex flex-col shrink-0 h-full
          transition-transform duration-200
          ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Brand */}
        <div className="px-4 py-5 border-b border-white/10 flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-white flex items-center justify-center text-black text-xs font-bold shrink-0">
            ⚖
          </div>
          <div>
            <p className="text-white text-sm font-semibold leading-none">ConformIA</p>
            <p className="text-white/40 text-[10px] mt-0.5">Assistant juridique</p>
          </div>
        </div>

        {/* New conversation */}
        <div className="px-3 pt-4 pb-2">
          <button
            onClick={() => { onNew(); onClose(); }}
            className="w-full flex items-center gap-2 text-white/80 hover:text-white hover:bg-white/10 text-sm px-3 py-2.5 rounded-lg transition-colors font-medium"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            Nouvelle conversation
          </button>
        </div>

        {/* History list */}
        <div className="flex-1 overflow-y-auto px-2 pb-4">
          {history.length === 0 ? (
            <p className="text-white/30 text-xs text-center mt-8 px-4">
              Aucune analyse pour l&apos;instant
            </p>
          ) : (
            <>
              <p className="text-white/30 text-[10px] uppercase tracking-widest font-medium px-2 py-2">
                Historique
              </p>
              <ul className="space-y-0.5">
                {history.map((item) => (
                  <li key={item.analysis_id}>
                    <button
                      onClick={() => { onSelect(item); onClose(); }}
                      className={`w-full text-left flex items-center gap-2.5 px-3 py-2.5 rounded-lg transition-colors group ${
                        activeId === item.analysis_id
                          ? "bg-white/15 text-white"
                          : "text-white/60 hover:bg-white/8 hover:text-white/90"
                      }`}
                    >
                      <StatusDot status={item.status} />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">{label(item)}</p>
                        <p className="text-[10px] text-white/30 mt-0.5">{fmt(item.created_at)}</p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </aside>
    </>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

const WELCOME: Msg = {
  kind: "bot",
  text: "Bonjour ! Posez-moi vos questions sur le droit du travail mauritanien, le Code des Obligations et des Contrats, ou la Convention Collective.\n\nVous pouvez aussi joindre un contrat (PDF, DOCX, TXT) pour une analyse de conformité complète.",
};

export default function Home() {
  const [messages, setMessages]   = useState<Msg[]>([WELCOME]);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [analysis, setAnalysis]   = useState<Analysis | null>(null);
  const [file, setFile]           = useState<File | null>(null);
  const [text, setText]           = useState("");
  const [busy, setBusy]           = useState(false);
  const [dragging, setDragging]   = useState(false);
  const [history, setHistory]     = useState<HistoryItem[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fileRef   = useRef<HTMLInputElement>(null);
  const textRef   = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const pollRef   = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch conversation history
  const refreshHistory = useCallback(async () => {
    try {
      const res = await fetch("/api/analyses");
      if (res.ok) setHistory(await res.json());
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { refreshHistory(); }, [refreshHistory]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const el = textRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [text]);

  // ── polling ──────────────────────────────────────────────────────────────
  const poll = useCallback(async (id: string) => {
    try {
      const res  = await fetch(`/api/analyses/${id}`);
      const data: Analysis = await res.json();
      if (data.status === "done") {
        setAnalysis(data);
        setMessages((prev) => [
          ...prev.filter((m) => m.kind !== "thinking"),
          { kind: "result", analysis: data },
          { kind: "bot", text: "Analyse terminée. Posez-moi vos questions sur ces résultats." },
        ]);
        setBusy(false);
        refreshHistory();
      } else if (data.status === "error") {
        setMessages((prev) => [
          ...prev.filter((m) => m.kind !== "thinking"),
          { kind: "error", text: `Erreur : ${data.error_log ?? "inconnue"}` },
        ]);
        setBusy(false);
        refreshHistory();
      } else {
        pollRef.current = setTimeout(() => poll(id), 2500);
      }
    } catch {
      pollRef.current = setTimeout(() => poll(id), 4000);
    }
  }, [refreshHistory]);

  useEffect(() => () => { if (pollRef.current) clearTimeout(pollRef.current); }, []);

  // ── load past analysis from sidebar ──────────────────────────────────────
  const loadAnalysis = useCallback(async (item: HistoryItem) => {
    if (pollRef.current) clearTimeout(pollRef.current);
    setBusy(false);
    setFile(null);
    setText("");
    setAnalysisId(item.analysis_id);

    setMessages([
      WELCOME,
      { kind: "user", text: `📄 ${item.doc_type}` },
    ]);

    try {
      const res  = await fetch(`/api/analyses/${item.analysis_id}`);
      const data: Analysis = await res.json();
      setAnalysis(data);

      if (data.status === "done") {
        setMessages([
          WELCOME,
          { kind: "user", text: `📄 ${item.doc_type}` },
          { kind: "result", analysis: data },
          { kind: "bot", text: "Analyse chargée. Posez-moi vos questions sur ces résultats." },
        ]);
      } else if (data.status === "error") {
        setMessages([
          WELCOME,
          { kind: "user", text: `📄 ${item.doc_type}` },
          { kind: "error", text: `Erreur : ${data.error_log ?? "inconnue"}` },
        ]);
      } else {
        setMessages([
          WELCOME,
          { kind: "user", text: `📄 ${item.doc_type}` },
          { kind: "bot", text: "Analyse en cours…" },
          { kind: "thinking" },
        ]);
        setBusy(true);
        poll(item.analysis_id);
      }
    } catch {
      setMessages((prev) => [...prev, { kind: "error", text: "Impossible de charger l'analyse." }]);
    }
  }, [poll]);

  // ── reset ─────────────────────────────────────────────────────────────────
  const reset = useCallback(() => {
    if (pollRef.current) clearTimeout(pollRef.current);
    setAnalysisId(null);
    setAnalysis(null);
    setFile(null);
    setText("");
    setBusy(false);
    setMessages([WELCOME]);
  }, []);

  // ── submit file ───────────────────────────────────────────────────────────
  const submitFile = async () => {
    if (!file || busy) return;
    setBusy(true);
    setMessages((prev) => [
      ...prev,
      { kind: "user", text: `📄 ${file.name}` },
      { kind: "thinking" },
    ]);
    setFile(null);
    setText("");

    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("jurisdiction", "mauritania_labor");
      const res  = await fetch("/api/analyses", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Erreur serveur");
      setAnalysisId(data.analysis_id);
      setMessages((prev) => [
        ...prev.filter((m) => m.kind !== "thinking"),
        { kind: "bot", text: "Analyse du contrat en cours…" },
        { kind: "thinking" },
      ]);
      poll(data.analysis_id);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setMessages((prev) => [
        ...prev.filter((m) => m.kind !== "thinking"),
        { kind: "error", text: msg },
      ]);
      setBusy(false);
    }
  };

  // ── keyword detection ────────────────────────────────────────────────────
  // Only trigger if the message is a DIRECT COMMAND, not a question about generating.
  const isQuestion = (msg: string) => {
    const lower = msg.toLowerCase();
    const questionMarkers = [
      "donne moi", "donnez moi", "dis moi", "qu'est", "comment", "que faut",
      "quels", "quelles", "combien", "explique", "expliquer", "informations",
      "renseignements", "pour me", "pour générer", "pour generer", "pour rédiger",
      "pour rediger", "pour créer", "?",
    ];
    return questionMarkers.some((w) => lower.includes(w));
  };

  const isCorrectRequest = (msg: string) => {
    if (isQuestion(msg)) return false;
    const kw = ["corrige", "corriger", "améliore", "rectifie", "version corrigée", "mise en conformité", "mettre en conformité", "corriger ce contrat"];
    return !!analysisId && kw.some((k) => msg.toLowerCase().includes(k));
  };

  const isGenerateRequest = (msg: string) => {
    if (isQuestion(msg)) return false;
    // Must start with or be a direct imperative command
    const lower = msg.toLowerCase().trim();
    const imperatives = ["génère", "genere", "génerer", "rédige", "redige", "rédiger", "crée un contrat", "cree un contrat", "rédige un contrat", "redige un contrat"];
    return imperatives.some((k) => lower.startsWith(k) || lower.includes(k));
  };

  // ── send chat ─────────────────────────────────────────────────────────────
  const sendChat = async () => {
    const msg = text.trim();
    if (!msg || busy) return;
    setText("");
    setBusy(true);
    setMessages((prev) => [...prev, { kind: "user", text: msg }, { kind: "thinking" }]);

    try {
      // ── Correction request ───────────────────────────────────────────────
      if (isCorrectRequest(msg)) {
        const res = await fetch(`/api/correct-document/${analysisId}`, { method: "POST" });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail ?? "Erreur serveur");
        }
        const blob = await res.blob();
        const disposition = res.headers.get("Content-Disposition") ?? "";
        const filenameMatch = disposition.match(/filename="([^"]+)"/);
        const filename = filenameMatch?.[1] ?? "contrat_corrige.docx";
        const blobUrl = URL.createObjectURL(blob);
        setMessages((prev) => [
          ...prev.filter((m) => m.kind !== "thinking"),
          { kind: "bot", text: "Voici la version corrigée de votre contrat, conforme au droit mauritanien :" },
          { kind: "document", filename, blobUrl },
        ]);

      // ── Generation request ───────────────────────────────────────────────
      } else if (isGenerateRequest(msg)) {
        const res = await fetch("/api/generate-document", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ description: msg }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail ?? "Erreur serveur");
        }
        const blob = await res.blob();
        const disposition = res.headers.get("Content-Disposition") ?? "";
        const filenameMatch = disposition.match(/filename="([^"]+)"/);
        const filename = filenameMatch?.[1] ?? "contrat.docx";
        const blobUrl = URL.createObjectURL(blob);
        setMessages((prev) => [
          ...prev.filter((m) => m.kind !== "thinking"),
          { kind: "bot", text: "Voici le contrat généré conformément au droit mauritanien :" },
          { kind: "document", filename, blobUrl },
        ]);

      // ── Normal chat ──────────────────────────────────────────────────────
      } else {
        const url = analysisId ? `/api/chat/${analysisId}` : "/api/chat";
        const res  = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: msg }),
        });
        const data = await res.json();
        const answer = res.ok ? data.answer : (data.detail ?? "Erreur serveur");
        setMessages((prev) => [
          ...prev.filter((m) => m.kind !== "thinking"),
          { kind: "bot", text: answer },
        ]);
      }
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : "Erreur de connexion.";
      setMessages((prev) => [
        ...prev.filter((m) => m.kind !== "thinking"),
        { kind: "error", text: errMsg },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const handleSend = () => {
    if (file)        { submitFile(); return; }
    if (text.trim()) { sendChat();   return; }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };

  const canSend     = !busy && (!!file || !!text.trim());
  const placeholder = busy ? "Réflexion en cours…" : "Message…";

  // ── render ────────────────────────────────────────────────────────────────
  return (
    <div
      className="flex h-screen bg-white overflow-hidden"
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setDragging(false); }}
      onDrop={onDrop}
    >
      {/* Sidebar */}
      <Sidebar
        history={history}
        activeId={analysisId}
        onSelect={loadAnalysis}
        onNew={reset}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main */}
      <div className="flex flex-col flex-1 min-w-0 h-full">

        {/* Header */}
        <header className="h-14 bg-white border-b border-neutral-100 px-4 flex items-center gap-3 shrink-0">
          {/* Mobile menu button */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden w-8 h-8 flex items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-100 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div className="flex-1 flex items-center gap-2 min-w-0">
            <span className="text-sm font-semibold text-neutral-900 truncate">
              {analysisId
                ? history.find((h) => h.analysis_id === analysisId)?.doc_type
                    ?.replace("_", " ") ?? "Analyse"
                : "Nouvelle conversation"}
            </span>
            {analysisId && (
              <span className="text-neutral-300 text-xs font-mono hidden sm:inline">
                #{analysisId.slice(0, 8)}
              </span>
            )}
          </div>

          {analysisId && (
            <button
              onClick={reset}
              className="text-xs text-neutral-400 hover:text-neutral-900 hover:bg-neutral-100 px-3 py-1.5 rounded-lg transition-colors font-medium shrink-0"
            >
              + Nouveau
            </button>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-2xl mx-auto px-4 py-8 space-y-5">
            {messages.map((m, i) => {
              if (m.kind === "user") return (
                <div key={i} className="flex justify-end">
                  <div className="max-w-[78%] bg-[#111] text-white text-sm px-4 py-3 rounded-2xl rounded-br-sm leading-relaxed whitespace-pre-wrap">
                    {m.text}
                  </div>
                </div>
              );

              if (m.kind === "bot") return (
                <div key={i} className="flex items-start gap-3">
                  <BotAvatar />
                  <div className="max-w-[82%] bg-neutral-50 text-neutral-900 text-sm px-4 py-3 rounded-2xl rounded-tl-sm border border-neutral-100 leading-relaxed whitespace-pre-wrap">
                    {m.text}
                  </div>
                </div>
              );

              if (m.kind === "thinking") return (
                <div key={i} className="flex items-start gap-3">
                  <BotAvatar />
                  <div className="bg-neutral-50 px-4 py-3.5 rounded-2xl rounded-tl-sm border border-neutral-100">
                    <ThinkingDots />
                  </div>
                </div>
              );

              if (m.kind === "error") return (
                <div key={i} className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-full bg-neutral-200 flex items-center justify-center shrink-0 text-neutral-500 text-xs">✕</div>
                  <div className="max-w-[82%] bg-neutral-50 text-red-600 text-sm px-4 py-3 rounded-2xl rounded-tl-sm border border-neutral-100 leading-relaxed">
                    {m.text}
                  </div>
                </div>
              );

              if (m.kind === "result") return (
                <div key={i} className="flex items-start gap-3">
                  <BotAvatar />
                  <div className="flex-1 min-w-0 bg-white px-4 py-4 rounded-2xl rounded-tl-sm border border-neutral-200 shadow-sm">
                    <FindingsCard analysis={m.analysis} />
                  </div>
                </div>
              );

              if (m.kind === "document") return (
                <div key={i} className="flex items-start gap-3">
                  <BotAvatar />
                  <div className="flex-1 min-w-0 max-w-sm">
                    <DocumentCard filename={m.filename} blobUrl={m.blobUrl} />
                  </div>
                </div>
              );

              return null;
            })}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input bar */}
        <div className={`shrink-0 bg-white px-4 pb-5 pt-2 transition-colors ${dragging ? "bg-neutral-50" : ""}`}>
          <div className="max-w-2xl mx-auto">
            <div className={`bg-white rounded-2xl border transition-all ${
              dragging
                ? "border-black ring-2 ring-black/10"
                : "border-neutral-200 focus-within:border-neutral-400 focus-within:ring-2 focus-within:ring-neutral-100"
            }`}>

              {/* file chip */}
              {file && (
                <div className="px-3 pt-3 pb-1">
                  <span className="inline-flex items-center gap-1.5 bg-neutral-100 text-neutral-700 text-xs px-2.5 py-1 rounded-lg font-medium">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {file.name}
                    <button onClick={() => setFile(null)} className="ml-0.5 text-neutral-400 hover:text-neutral-700 leading-none">✕</button>
                  </span>
                </div>
              )}

              {/* input row */}
              <div className="flex items-end px-2 py-2 gap-1">
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])}
                />
                <button
                  onClick={() => fileRef.current?.click()}
                  disabled={busy}
                  title="Joindre un document"
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-neutral-400 hover:text-neutral-700 hover:bg-neutral-100 transition-colors disabled:opacity-30 shrink-0"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                </button>

                <textarea
                  ref={textRef}
                  rows={1}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={placeholder}
                  disabled={busy}
                  className="flex-1 bg-transparent resize-none outline-none text-sm text-neutral-900 placeholder:text-neutral-400 py-1.5 leading-relaxed disabled:cursor-not-allowed max-h-40"
                />

                <button
                  onClick={handleSend}
                  disabled={!canSend}
                  className="w-8 h-8 flex items-center justify-center rounded-lg bg-[#111] hover:bg-black disabled:bg-neutral-100 text-white disabled:text-neutral-300 transition-colors shrink-0"
                >
                  {busy ? (
                    <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                  ) : (
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 10.5L12 3m0 0l7.5 7.5M12 3v18" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <p className="text-xs text-center text-neutral-400 mt-2">
              PDF · DOCX · TXT — 10 Mo max · Glissez-déposez un fichier
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
