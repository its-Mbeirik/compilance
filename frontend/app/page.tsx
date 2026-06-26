"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth, useApiFetch } from "./contexts/auth";
import ReactMarkdown from "react-markdown";

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

type Extracted = {
  type_contrat:         string;
  employeur:            string;
  employe:              string;
  poste:                string;
  date_debut:           string | null;
  date_fin:             string | null;
  duree_mois:           number | null;
  salaire_mensuel_mru: number | null;
  periode_essai_mois:   number | null;
  est_cadre:            boolean;
  age_employe:          number | null;
  visa_inspection:      boolean | null;
};

type Analysis = {
  id: string;
  status: string;
  jurisdiction: string;
  doc_type: string;
  findings: Finding[];
  extracted: Extracted | null;
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
  | { kind: "user";      text: string }
  | { kind: "bot";       text: string }
  | { kind: "thinking" }
  | { kind: "result";    analysis: Analysis }
  | { kind: "document";  filename: string; blobUrl?: string; fileId?: string }
  | { kind: "file_ref";  filename: string; analysisId: string; fileId?: string }
  | { kind: "error";     text: string };

// ── localStorage session helpers ───────────────────────────────────────────

const CHAT_KEY = (id: string) => `conformia_chat_${id}`;
const FILE_KEY = (id: string) => `conformia_file_${id}`;

function saveSession(id: string, msgs: Msg[]) {
  try {
    // Exclude thinking bubbles and blob-only documents (blobs die on refresh).
    // Documents with a server-side fileId are safe to persist.
    const saveable = msgs.filter(
      (m) => m.kind !== "thinking" &&
             !(m.kind === "document" && !m.fileId)
    );
    localStorage.setItem(CHAT_KEY(id), JSON.stringify(saveable));
  } catch { /* localStorage full or unavailable */ }
}

function loadSession(id: string): Msg[] | null {
  try {
    const raw = localStorage.getItem(CHAT_KEY(id));
    return raw ? (JSON.parse(raw) as Msg[]) : null;
  } catch { return null; }
}

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

// ── Contract bilan ────────────────────────────────────────────────────────

const CONTRACT_TYPE_COLOR: Record<string, string> = {
  CDI:   "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  CDD:   "bg-blue-50 text-blue-700 ring-1 ring-blue-200",
  CTT:   "bg-purple-50 text-purple-700 ring-1 ring-purple-200",
  Stage: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  Autre: "bg-neutral-100 text-neutral-600 ring-1 ring-neutral-200",
};

function ContractBilan({ extracted }: { extracted: Extracted }) {
  const fmtDate = (d: string | null): string | null => {
    if (!d || d.trim() === "") return null;
    // Try ISO and common formats
    const parsed = new Date(d);
    if (!isNaN(parsed.getTime())) {
      return parsed.toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" });
    }
    // Try DD/MM/YYYY (common in French contracts)
    const dmy = d.match(/^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$/);
    if (dmy) {
      const parsed2 = new Date(`${dmy[3]}-${dmy[2].padStart(2,"0")}-${dmy[1].padStart(2,"0")}`);
      if (!isNaN(parsed2.getTime()))
        return parsed2.toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" });
    }
    // Return raw string if it looks like something meaningful, else null
    return d.length > 2 ? d : null;
  };

  const fmtSalaire = (v: number | null) =>
    v != null ? new Intl.NumberFormat("fr-FR").format(v) + " MRU" : null;

  const rows: { label: string; value: string | null }[] = [
    { label: "Employeur",      value: extracted.employeur || null },
    { label: "Employé",        value: extracted.employe   || null },
    { label: "Poste",          value: extracted.poste     || null },
    { label: "Date de début",  value: fmtDate(extracted.date_debut) ?? (extracted.date_debut ? "Non spécifié" : null) },
    ...(extracted.date_fin != null
      ? [{ label: "Date de fin", value: fmtDate(extracted.date_fin) ?? "Non spécifié" }]
      : []),
    ...(extracted.duree_mois != null
      ? [{ label: "Durée", value: `${extracted.duree_mois} mois` }]
      : []),
    { label: "Salaire mensuel",   value: fmtSalaire(extracted.salaire_mensuel_mru) },
    ...(extracted.periode_essai_mois != null
      ? [{ label: "Période d'essai", value: `${extracted.periode_essai_mois} mois` }]
      : []),
    ...(extracted.age_employe != null
      ? [{ label: "Âge de l'employé", value: `${extracted.age_employe} ans` }]
      : []),
    ...(extracted.visa_inspection != null
      ? [{ label: "Visa inspection", value: extracted.visa_inspection ? "Oui" : "Non" }]
      : []),
  ].filter((r) => r.value !== null);

  const typeColor = CONTRACT_TYPE_COLOR[extracted.type_contrat] ?? CONTRACT_TYPE_COLOR["Autre"];

  return (
    <div className="mb-4 pb-4 border-b border-neutral-100">
      <div className="flex items-center gap-2 mb-3">
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${typeColor}`}>
          {extracted.type_contrat}
        </span>
        {extracted.est_cadre && (
          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-neutral-100 text-neutral-500">
            Cadre
          </span>
        )}
        <span className="text-xs text-neutral-400 font-medium ml-auto">Résumé du contrat</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5">
        {rows.map(({ label, value }) => (
          <div key={label} className="flex items-baseline gap-1.5 min-w-0">
            <span className="text-[11px] text-neutral-400 shrink-0 w-32">{label}</span>
            <span className="text-xs font-medium text-neutral-800 truncate">{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Abbreviate long article IDs for display: "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10" → "Art. 10 · CT"
const CODE_ABBREV: Record<string, string> = {
  CODE_TRAVAIL_MR:    "CT",
  COC_MR:             "COC",
  CODE_COMMERCE_MR:   "CC",
  CONV_COLLECTIVE:    "CCG",
  CONVENTIONS_ILO:    "OIT",
};
function abbreviateArticleId(id: string): string {
  // Expected format: JURISDICTION-CODE_NAME-ARTICLE_NUMBER
  const parts = id.split("-");
  if (parts.length < 3) return id;
  const articleNum = parts[parts.length - 1];
  // Code name is everything between first and last dash segment
  const codeParts = parts.slice(1, parts.length - 1).join("_");
  const abbrev = CODE_ABBREV[codeParts] ?? codeParts.replace("MAURITANIA_LABOR_", "");
  return `Art. ${articleNum} · ${abbrev}`;
}

// ── Findings card ──────────────────────────────────────────────────────────

function FindingsCard({ analysis, onDownloadPdf }: { analysis: Analysis; onDownloadPdf: () => void }) {
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
        <button
          onClick={onDownloadPdf}
          className="ml-auto text-xs text-neutral-500 hover:text-neutral-900 font-medium flex items-center gap-1 shrink-0 underline underline-offset-2"
        >
          Rapport PDF
        </button>
      </div>

      {analysis.findings.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-neutral-200 max-w-full">
          <table className="w-full text-xs table-fixed">
            <colgroup>
              <col className="w-20" />
              <col className="w-28" />
              <col className="w-24" />
              <col className="w-28" />
              <col />
            </colgroup>
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
                  <td className="px-3 py-2.5 font-mono text-neutral-400 truncate">{f.clause_id}</td>
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
                  <td
                    className="px-3 py-2.5 font-mono text-neutral-700 font-semibold truncate"
                    title={f.cited_article_id}
                  >
                    {abbreviateArticleId(f.cited_article_id)}
                  </td>
                  <td className="px-3 py-2.5 text-neutral-600">
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

function DocumentCard({ filename, blobUrl, fileId }: { filename: string; blobUrl?: string; fileId?: string }) {
  const apiFetch = useApiFetch();
  const available = !!(fileId || blobUrl);

  const handleDownload = useCallback(async () => {
    if (fileId) {
      // Authenticated fetch — sends Authorization header
      try {
        const res = await apiFetch(`/api/files/doc/${fileId}`);
        if (!res.ok) { alert("Fichier non disponible."); return; }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = filename; a.click();
        URL.revokeObjectURL(url);
      } catch { alert("Erreur lors du téléchargement."); }
    } else if (blobUrl) {
      const a = document.createElement("a");
      a.href = blobUrl; a.download = filename; a.click();
    }
  }, [fileId, blobUrl, filename, apiFetch]);

  return (
    <div className="flex items-center gap-3 bg-neutral-50 border border-neutral-200 rounded-xl px-4 py-3">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${available ? "bg-black" : "bg-neutral-300"}`}>
        <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-neutral-900 truncate">{filename}</p>
        <p className="text-xs text-neutral-400 mt-0.5">
          {available ? "Document Word · prêt à télécharger" : "Fichier non disponible"}
        </p>
      </div>
      {available ? (
        <button
          onClick={handleDownload}
          className="flex items-center gap-1.5 bg-black text-white text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-neutral-800 transition-colors shrink-0"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Télécharger
        </button>
      ) : (
        <span className="flex items-center gap-1.5 border border-neutral-200 text-neutral-400 text-xs font-medium px-3 py-1.5 rounded-lg shrink-0 cursor-not-allowed">
          Indisponible
        </span>
      )}
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
  userName,
  userRole,
  onLogout,
}: {
  history:  HistoryItem[];
  activeId: string | null;
  onSelect: (item: HistoryItem) => void;
  onNew:    () => void;
  open:     boolean;
  onClose:  () => void;
  userName: string;
  userRole: string;
  onLogout: () => void;
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

        {/* User info + links */}
        <div className="px-4 py-4 border-t border-white/10 shrink-0">
          <p className="text-white/40 text-xs truncate mb-1">{userName}</p>
          <div className="text-[10px] bg-white/10 text-white/50 px-2 py-0.5 rounded-full w-fit mb-2">
            {userRole === "sub_user" ? "Assistant" : "Utilisateur"}
          </div>
          <div className="flex flex-col gap-1">
            {userRole === "user" && (
              <a href="/sub-users" className="text-xs text-white/40 hover:text-white transition-colors">
                Assistants
              </a>
            )}
            <a href="/settings" className="text-xs text-white/40 hover:text-white transition-colors">
              Paramètres
            </a>
            <button onClick={onLogout} className="text-xs text-white/40 hover:text-white transition-colors text-left mt-1">
              Déconnexion
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

const WELCOME: Record<"fr" | "ar", Msg> = {
  fr: {
    kind: "bot",
    text: "Bonjour ! Posez-moi vos questions sur le droit du travail mauritanien, le Code des Obligations et des Contrats, ou la Convention Collective.\n\nVous pouvez aussi joindre un contrat (PDF, DOCX, TXT) pour une analyse de conformité complète.",
  },
  ar: {
    kind: "bot",
    text: "مرحباً! يمكنكم طرح أسئلتكم حول قانون العمل الموريتاني، ومدونة الالتزامات والعقود، أو الاتفاقية الجماعية العامة للعمل.\n\nكما يمكنكم إرفاق عقد (PDF أو DOCX أو TXT) لتحليل مدى امتثاله للتشريعات.",
  },
};

export default function Home() {
  const { user, loading, logout } = useAuth();
  const apiFetch = useApiFetch();
  const router = useRouter();

  const [messages, setMessages]   = useState<Msg[]>([WELCOME["fr"]]);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [analysis, setAnalysis]   = useState<Analysis | null>(null);
  const [file, setFile]           = useState<File | null>(null);
  const [text, setText]           = useState("");
  const [busy, setBusy]           = useState(false);
  const [dragging, setDragging]   = useState(false);
  const [history, setHistory]     = useState<HistoryItem[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [awaitingDocGen, setAwaitingDocGen] = useState(false);

  // Persist awaitingDocGen per analysis in sessionStorage so it survives sidebar navigation
  useEffect(() => {
    if (!analysisId) return;
    if (awaitingDocGen) sessionStorage.setItem(`conformia_aw_${analysisId}`, "1");
    else sessionStorage.removeItem(`conformia_aw_${analysisId}`);
  }, [awaitingDocGen, analysisId]);

  // Auth guard: redirect unauthenticated or pending users
  useEffect(() => {
    if (loading) return;
    if (!user)                      { router.replace("/login");   return; }
    if (user.role === "admin")      { router.replace("/admin");   return; }
    if (user.status !== "approved") { router.replace("/pending"); return; }
  }, [user, loading, router]);

  const fileRef        = useRef<HTMLInputElement>(null);
  const textRef        = useRef<HTMLTextAreaElement>(null);
  const bottomRef      = useRef<HTMLDivElement>(null);
  const pollRef        = useRef<ReturnType<typeof setTimeout> | null>(null);
  const recognitionRef = useRef<any>(null);

  const [isListening,    setIsListening]    = useState(false);
  const [speakingIndex,  setSpeakingIndex]  = useState<number | null>(null);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [lang,           setLang]           = useState<"fr" | "ar">("fr");

  useEffect(() => {
    setVoiceSupported(
      typeof window !== "undefined" &&
      !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)
    );
    return () => { window.speechSynthesis?.cancel(); };
  }, []);

  const toggleVoice = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }
    const rec = new SR();
    rec.lang = lang === "ar" ? "ar-SA" : "fr-FR";
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e: any) => {
      const transcript: string = e.results[0][0].transcript;
      setText((prev) => prev ? `${prev} ${transcript}` : transcript);
    };
    rec.onend  = () => setIsListening(false);
    rec.onerror = () => setIsListening(false);
    recognitionRef.current = rec;
    rec.start();
    setIsListening(true);
  }, [isListening]);

  const speak = useCallback((text: string, idx: number) => {
    if (!window.speechSynthesis) return;
    if (speakingIndex === idx) {
      window.speechSynthesis.cancel();
      setSpeakingIndex(null);
      return;
    }
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = lang === "ar" ? "ar-SA" : "fr-FR";
    utt.rate = 1.0;
    utt.onend = () => setSpeakingIndex(null);
    utt.onerror = () => setSpeakingIndex(null);
    setSpeakingIndex(idx);
    window.speechSynthesis.speak(utt);
  }, [speakingIndex]);

  // ── Persist messages to localStorage ────────────────────────────────────
  useEffect(() => {
    if (!analysisId || messages.length <= 1) return;
    saveSession(analysisId, messages);
  }, [messages, analysisId]);

  // ── Download original uploaded file ──────────────────────────────────────
  const handleDownloadFile = useCallback(async (aid: string, filename: string) => {
    try {
      const res = await apiFetch(`/api/files/${aid}`);
      if (!res.ok) throw new Error("Fichier non disponible");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Impossible de télécharger le fichier original.");
    }
  }, [apiFetch]);

  // Fetch conversation history
  const refreshHistory = useCallback(async () => {
    try {
      const res = await apiFetch("/api/analyses");
      if (res.ok) setHistory(await res.json());
    } catch { /* ignore */ }
  }, [apiFetch]);

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
      const res  = await apiFetch(`/api/analyses/${id}`);
      const data: Analysis = await res.json();
      if (data.status === "done") {
        setAnalysis(data);
        const ext = data.extracted;
        const bilanLine = ext?.type_contrat
          ? `Contrat **${ext.type_contrat}** — ${ext.employeur} / ${ext.employe}.`
          : "";
        setMessages((prev) => [
          ...prev.filter((m) => m.kind !== "thinking"),
          { kind: "result", analysis: data },
          { kind: "bot", text: `${bilanLine ? bilanLine + "\n\n" : ""}Analyse terminée. Posez-moi vos questions sur ces résultats.`.trim() },
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
  }, [refreshHistory, apiFetch]);

  useEffect(() => () => { if (pollRef.current) clearTimeout(pollRef.current); }, []);

  // ── load past analysis from sidebar ──────────────────────────────────────
  const loadAnalysis = useCallback(async (item: HistoryItem) => {
    if (pollRef.current) clearTimeout(pollRef.current);
    setBusy(false);
    setFile(null);
    setText("");
    setAnalysisId(item.analysis_id);
    setAwaitingDocGen(sessionStorage.getItem(`conformia_aw_${item.analysis_id}`) === "1");

    // ── Try to restore full session from localStorage ──────────────────────
    const stored = loadSession(item.analysis_id);
    if (stored && stored.length > 1) {
      setMessages(stored);
      try {
        const res  = await apiFetch(`/api/analyses/${item.analysis_id}`);
        const data: Analysis = await res.json();
        setAnalysis(data);
        if (data.status === "running" || data.status === "pending") {
          setMessages((prev) => [...prev, { kind: "thinking" }]);
          setBusy(true);
          poll(item.analysis_id);
        }
      } catch { /* ignore — messages already restored */ }
      return;
    }

    // ── Fallback: reconstruct from API ─────────────────────────────────────
    const filename = localStorage.getItem(FILE_KEY(item.analysis_id)) ?? item.doc_type;
    setMessages([WELCOME[lang], { kind: "file_ref", filename, analysisId: item.analysis_id }]);

    try {
      const res  = await apiFetch(`/api/analyses/${item.analysis_id}`);
      const data: Analysis = await res.json();
      setAnalysis(data);

      if (data.status === "done") {
        setMessages([
          WELCOME[lang],
          { kind: "file_ref", filename, analysisId: item.analysis_id },
          { kind: "result", analysis: data },
          { kind: "bot", text: lang === "ar" ? "تم تحميل التحليل. يمكنكم طرح أسئلتكم." : "Analyse chargée. Posez-moi vos questions sur ces résultats." },
        ]);
      } else if (data.status === "error") {
        setMessages([
          WELCOME[lang],
          { kind: "file_ref", filename, analysisId: item.analysis_id },
          { kind: "error", text: `${lang === "ar" ? "خطأ" : "Erreur"} : ${data.error_log ?? (lang === "ar" ? "غير معروف" : "inconnue")}` },
        ]);
      } else {
        setMessages([
          WELCOME[lang],
          { kind: "file_ref", filename, analysisId: item.analysis_id },
          { kind: "bot", text: lang === "ar" ? "جارٍ تحليل العقد…" : "Analyse en cours…" },
          { kind: "thinking" },
        ]);
        setBusy(true);
        poll(item.analysis_id);
      }
    } catch {
      setMessages((prev) => [...prev, { kind: "error", text: lang === "ar" ? "تعذّر تحميل التحليل." : "Impossible de charger l'analyse." }]);
    }
  }, [poll, apiFetch, lang]);

  // ── reset ─────────────────────────────────────────────────────────────────
  const reset = useCallback(() => {
    if (pollRef.current) clearTimeout(pollRef.current);
    setAnalysisId(null);
    setAnalysis(null);
    setFile(null);
    setText("");
    setBusy(false);
    setAwaitingDocGen(false);
    setMessages([WELCOME[lang]]);
  }, [lang]);

  // ── submit file ───────────────────────────────────────────────────────────
  const submitFile = async () => {
    if (!file || busy) return;
    const filename    = file.name;
    const initialText = text.trim();

    setBusy(true);
    const userText = initialText ? `📄 ${filename}\n${initialText}` : `📄 ${filename}`;
    setMessages((prev) => [...prev, { kind: "user", text: userText }, { kind: "thinking" }]);
    setFile(null);
    setText("");

    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("jurisdiction", "mauritania_labor");
      fd.append("language", lang);
      const res  = await apiFetch("/api/analyses", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Erreur serveur");

      const aid = data.analysis_id;
      const fid: string | undefined = data.file_id;
      setAnalysisId(aid);
      // Persist filename for history restore
      try { localStorage.setItem(FILE_KEY(aid), filename); } catch { /* ignore */ }

      setMessages((prev) => [
        ...prev.filter((m) => m.kind !== "thinking"),
        { kind: "file_ref", filename, analysisId: aid, fileId: fid },
        { kind: "bot", text: lang === "ar" ? "جارٍ تحليل العقد…" : "Analyse du contrat en cours…" },
        { kind: "thinking" },
      ]);
      setBusy(false); // Allow typing while analysis runs
      poll(aid);
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
  // Strip diacritics for accent-insensitive matching (é/è/ê → e, etc.)
  const stripAccents = (s: string) =>
    s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();

  // Block only clearly informational questions (no "?" — polite requests like
  // "Pouvez-vous générer...?" must reach generate/correct, not the chat LLM)
  const isQuestion = (msg: string) => {
    const n = stripAccents(msg);
    const infoMarkers = [
      "comment", "qu'est", "que faut", "quels", "quelles", "combien",
      "explique", "expliquer", "informations", "renseignements",
      "donnez moi", "dis moi",
      "pour me", "pour generer", "pour rediger", "pour creer",
    ];
    return infoMarkers.some((w) => n.includes(w));
  };

  const isCorrectRequest = (msg: string) => {
    if (isQuestion(msg)) return false;
    const n = stripAccents(msg);
    const kw = [
      "corrige", "corriger", "corrigez",
      "ameliore", "ameliorez", "ameliorer",
      "rectifie", "rectifiez",
      "version corrigee", "rapport corrige", "contrat corrige",
      "clauses corrigees", "clause corrigee",
      "mise en conformite", "mettre en conformite",
    ];
    return !!analysisId && kw.some((k) => n.includes(k));
  };

  const isConfirmation = (msg: string) => {
    const n = stripAccents(msg);
    return ["oui", "yes", "ok ", "okay", "confirme", "vas-y", "vasy", "go ",
            "bien sur", "d accord", "daccord", "allez", "parfait",
            "je confirme", "genere", "generer", "telecharger", "svp",
            "donne", "done", "version corrigee", "contrat corrige", "envoie"].some(
      (k) => n.includes(k) || n === k.trim()
    );
  };

  const isRejection = (msg: string) => {
    const n = stripAccents(msg);
    return ["non", "no ", "pas maintenant", "annule", "annuler", "cancel",
            "stop", "oublie", "laisse tomber", "pas besoin", "pas de docx",
            "ne genere pas", "ne corrige pas"].some(
      (k) => n.includes(k) || n === k.trim()
    );
  };

  const isGenerateRequest = (msg: string) => {
    if (isQuestion(msg)) return false;
    const n = stripAccents(msg);
    // Direct generation verbs — match anywhere in message
    const directVerbs = ["genere", "generez", "generer", "redige", "redigez", "rediger"];
    if (directVerbs.some((v) => n.includes(v))) return true;
    // Action verb + document type combinations
    const actionVerbs = ["cree", "creez", "creer", "fais", "faites", "faire",
                         "etablis", "etablissez", "etablir", "prepare", "preparez",
                         "preparer", "produis", "produire", "ecris", "ecrivez"];
    const docTypes = ["contrat", "cdi", "cdd", "convention"];
    return actionVerbs.some((v) => n.includes(v)) && docTypes.some((d) => n.includes(d));
  };

  // ── send chat ─────────────────────────────────────────────────────────────
  const sendChat = async () => {
    const msg = text.trim();
    if (!msg || busy) return;
    setText("");
    setBusy(true);
    setMessages((prev) => [...prev, { kind: "user", text: msg }, { kind: "thinking" }]);

    try {
      // ── Rejection: user cancels pending Phase 2 confirmation ─────────────
      if (awaitingDocGen && isRejection(msg)) {
        setAwaitingDocGen(false);
        if (analysisId) sessionStorage.removeItem(`conformia_aw_${analysisId}`);
        setMessages((prev) => [
          ...prev.filter((m) => m.kind !== "thinking"),
          { kind: "bot", text: lang === "ar"
            ? "حسناً، تم الإلغاء. يمكنك طلب التصحيح مجدداً في أي وقت."
            : "D'accord, génération annulée. Vous pouvez relancer la correction quand vous le souhaitez." },
        ]);
        setBusy(false);
        return;
      }

      // ── Phase 2 : user confirms document generation ──────────────────────
      if (awaitingDocGen && isConfirmation(msg)) {
        const res = await apiFetch(`/api/correct-document/${analysisId}`, { method: "POST" });
        if (!res.ok) {
          let detail = "Erreur lors de la génération du document";
          try { detail = (await res.json()).detail ?? detail; } catch { /* */ }
          throw new Error(detail);
        }
        const fileId = res.headers.get("X-File-Id") ?? undefined;
        const blob = await res.blob();
        const disposition = res.headers.get("Content-Disposition") ?? "";
        const filename = disposition.match(/filename="([^"]+)"/)?.[1] ?? "contrat_corrige.docx";
        const blobUrl = fileId ? undefined : URL.createObjectURL(blob);
        setAwaitingDocGen(false);
        setMessages((prev) => [
          ...prev.filter((m) => m.kind !== "thinking"),
          { kind: "bot", text: lang === "ar" ? "إليك النسخة المصحَّحة من عقدك المتوافقة مع القانون الموريتاني :" : "Voici la version corrigée de votre contrat, conforme au droit mauritanien :" },
          { kind: "document", filename, blobUrl, fileId },
        ]);

      // ── Phase 1 : correction OR any generation when an analysis is active ──
      // Route ALL generation/correction requests through Phase 1 when an
      // analysisId is set — never generate directly from the description.
      } else if (isCorrectRequest(msg) || (!!analysisId && isGenerateRequest(msg))) {
        const res = await apiFetch(`/api/preview-corrections/${analysisId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: msg, language: lang }),
        });
        if (!res.ok) {
          // Friendly message instead of raw error — keep state clean for retry
          setMessages((prev) => [
            ...prev.filter((m) => m.kind !== "thinking"),
            { kind: "bot", text: lang === "ar"
              ? "قبل إنشاء المستند، يجب أن أعرض عليك التصحيحات المقترحة أولاً. يُرجى تجربة طلب التصحيح مرة أخرى."
              : "Avant de générer le document, je dois d'abord vous montrer les corrections proposées. Veuillez relancer votre demande de correction." },
          ]);
          setBusy(false);
          return;
        }
        const data = await res.json();
        setMessages((prev) => [
          ...prev.filter((m) => m.kind !== "thinking"),
          { kind: "bot", text: data.preview ?? "" },
        ]);
        setAwaitingDocGen(true);

      // ── Generation request (no active analysis — fresh contract) ─────────
      } else if (isGenerateRequest(msg)) {
        const res = await apiFetch("/api/generate-document", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ description: msg, language: lang }),
        });
        if (!res.ok) {
          let detail = "Erreur lors de la génération";
          try { detail = (await res.json()).detail ?? detail; } catch { /* non-JSON body */ }
          throw new Error(detail);
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
        // If user was asked for confirmation but replied with something else,
        // keep awaitingDocGen — the confirmation buttons remain visible.
        const isAnalysisDone = analysis?.status === "done";
        const url = (analysisId && isAnalysisDone) ? `/api/chat/${analysisId}` : "/api/chat";
        const res  = await apiFetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: msg, language: lang }),
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

  // Called by the confirmation button (Phase 2, button path)
  const handleGenerateDoc = useCallback(async () => {
    if (!analysisId || busy) return;
    setBusy(true);
    setAwaitingDocGen(false);
    setMessages((prev) => [...prev, { kind: "thinking" }]);
    try {
      const res = await apiFetch(`/api/correct-document/${analysisId}`, { method: "POST" });
      if (!res.ok) {
        let detail = "Erreur lors de la génération du document";
        try { detail = (await res.json()).detail ?? detail; } catch { /* */ }
        throw new Error(detail);
      }
      const fileId = res.headers.get("X-File-Id") ?? undefined;
      const blob = await res.blob();
      const disposition = res.headers.get("Content-Disposition") ?? "";
      const filename = disposition.match(/filename="([^"]+)"/)?.[1] ?? "contrat_corrige.docx";
      const blobUrl = fileId ? undefined : URL.createObjectURL(blob);
      setMessages((prev) => [
        ...prev.filter((m) => m.kind !== "thinking"),
        { kind: "bot", text: lang === "ar" ? "إليك النسخة المصحَّحة من عقدك المتوافقة مع القانون الموريتاني :" : "Voici la version corrigée de votre contrat, conforme au droit mauritanien :" },
        { kind: "document", filename, blobUrl, fileId },
      ]);
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : "Erreur de connexion.";
      setMessages((prev) => [
        ...prev.filter((m) => m.kind !== "thinking"),
        { kind: "error", text: errMsg },
      ]);
    } finally {
      setBusy(false);
    }
  }, [analysisId, apiFetch, lang, busy]);

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
  const placeholder = isListening
    ? (lang === "ar" ? "جارٍ الاستماع…" : "Écoute en cours…")
    : busy
    ? (lang === "ar" ? "جارٍ المعالجة…" : "Réflexion en cours…")
    : (lang === "ar" ? "اكتب رسالتك…" : "Message…");

  // Wait for auth before rendering (redirects are handled in useEffect)
  if (loading || !user) return null;

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
        userName={user.name}
        userRole={user.role}
        onLogout={logout}
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

          {/* Language toggle */}
          <button
            onClick={() => setLang(l => l === "fr" ? "ar" : "fr")}
            title={lang === "fr" ? "Passer en arabe" : "التبديل إلى الفرنسية"}
            className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg border border-neutral-200 hover:bg-neutral-50 transition-colors shrink-0 text-neutral-600"
          >
            <span>{lang === "fr" ? "🇫🇷 FR" : "🇲🇷 AR"}</span>
            <span className="text-neutral-300">→</span>
            <span>{lang === "fr" ? "AR" : "FR"}</span>
          </button>

          {analysisId && (
            <button
              onClick={reset}
              className="text-xs text-neutral-400 hover:text-neutral-900 hover:bg-neutral-100 px-3 py-1.5 rounded-lg transition-colors font-medium shrink-0"
            >
              {lang === "ar" ? "+ جديد" : "+ Nouveau"}
            </button>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-2xl mx-auto px-4 py-8 space-y-5">
            {messages.map((m, i) => {
              if (m.kind === "user") return (
                <div key={i} className="flex justify-end">
                  <div dir="auto" className="max-w-[78%] bg-[#111] text-white text-sm px-4 py-3 rounded-2xl rounded-br-sm leading-relaxed whitespace-pre-wrap">
                    {m.text}
                  </div>
                </div>
              );

              if (m.kind === "bot") return (
                <div key={i} className="flex items-start gap-3 group">
                  <BotAvatar />
                  <div dir="auto" className="max-w-[82%] bg-neutral-50 text-neutral-900 text-sm px-4 py-3 rounded-2xl rounded-tl-sm border border-neutral-100 leading-relaxed">
                    <ReactMarkdown
                      components={{
                        h1: ({children}) => <h1 className="text-base font-bold mt-3 mb-1 first:mt-0">{children}</h1>,
                        h2: ({children}) => <h2 className="text-sm font-bold mt-2.5 mb-1 first:mt-0">{children}</h2>,
                        h3: ({children}) => <h3 className="text-sm font-semibold mt-2 mb-0.5 first:mt-0">{children}</h3>,
                        p:  ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                        strong: ({children}) => <strong className="font-semibold text-neutral-900">{children}</strong>,
                        em: ({children}) => <em className="italic">{children}</em>,
                        ul: ({children}) => <ul className="list-disc list-outside pl-4 mb-2 space-y-0.5">{children}</ul>,
                        ol: ({children}) => <ol className="list-decimal list-outside pl-4 mb-2 space-y-0.5">{children}</ol>,
                        li: ({children}) => <li className="leading-relaxed">{children}</li>,
                        code: ({children}) => <code className="bg-neutral-200 text-neutral-800 px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
                        hr:  () => <hr className="border-neutral-200 my-2" />,
                      }}
                    >
                      {m.text}
                    </ReactMarkdown>
                  </div>
                  <button
                    onClick={() => speak(m.text, i)}
                    title={speakingIndex === i ? "Arrêter" : "Écouter"}
                    className={`opacity-0 group-hover:opacity-100 mt-1 w-7 h-7 flex items-center justify-center rounded-lg transition-all shrink-0 ${
                      speakingIndex === i
                        ? "bg-black text-white"
                        : "text-neutral-400 hover:text-neutral-700 hover:bg-neutral-100"
                    }`}
                  >
                    {speakingIndex === i ? (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                        <rect x="6" y="4" width="4" height="16" rx="1"/>
                        <rect x="14" y="4" width="4" height="16" rx="1"/>
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072M12 6v12m0 0l-3-3m3 3l3-3M9.172 9.172a4 4 0 000 5.656"/>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M11 5a7 7 0 010 14"/>
                      </svg>
                    )}
                  </button>
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

              if (m.kind === "file_ref") return (
                <div key={i} className="flex justify-end">
                  <div className="flex items-center gap-2.5 bg-[#111] text-white text-sm px-4 py-2.5 rounded-2xl rounded-br-sm max-w-[78%]">
                    <svg className="w-4 h-4 shrink-0 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="truncate text-xs font-medium">{m.filename}</span>
                    <button
                      onClick={() => handleDownloadFile(m.analysisId, m.filename)}
                      title="Télécharger le fichier original"
                      className="shrink-0 text-white/40 hover:text-white transition-colors ml-1"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                    </button>
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

              if (m.kind === "result") {
                const handleDownloadPdf = async () => {
                  try {
                    const res = await apiFetch(`/api/analyses/${m.analysis.id}/report?fmt=pdf`);
                    if (!res.ok) throw new Error("Erreur lors du téléchargement");
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `rapport_${m.analysis.id.slice(0, 8)}.pdf`;
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch {
                    alert("Impossible de télécharger le rapport PDF.");
                  }
                };
                return (
                  <div key={i} className="flex items-start gap-3">
                    <BotAvatar />
                    <div className="flex-1 min-w-0 overflow-hidden bg-white px-4 py-4 rounded-2xl rounded-tl-sm border border-neutral-200 shadow-sm">
                      {m.analysis.extracted && Object.keys(m.analysis.extracted).length > 0 && (
                        <ContractBilan extracted={m.analysis.extracted as Extracted} />
                      )}
                      <FindingsCard analysis={m.analysis} onDownloadPdf={handleDownloadPdf} />
                    </div>
                  </div>
                );
              }

              if (m.kind === "document") return (
                <div key={i} className="flex items-start gap-3">
                  <BotAvatar />
                  <div className="flex-1 min-w-0 max-w-sm">
                    <DocumentCard filename={m.filename} blobUrl={m.blobUrl} fileId={m.fileId} />
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

            {/* Phase 2 confirmation buttons */}
            {awaitingDocGen && !busy && (
              <div className="flex gap-2 mb-2">
                <button
                  onClick={handleGenerateDoc}
                  className="flex-1 flex items-center justify-center gap-1.5 bg-black text-white text-sm font-medium py-2.5 rounded-xl hover:bg-neutral-800 transition-colors"
                >
                  <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {lang === "ar" ? "نعم، أنشئ ملف .docx" : "Oui, générer le .docx"}
                </button>
                <button
                  onClick={() => {
                    setAwaitingDocGen(false);
                    if (analysisId) sessionStorage.removeItem(`conformia_aw_${analysisId}`);
                    setMessages((prev) => [
                      ...prev,
                      { kind: "bot", text: lang === "ar"
                        ? "حسناً، تم الإلغاء. يمكنك طلب التصحيح مجدداً في أي وقت."
                        : "D'accord, génération annulée. Vous pouvez relancer la correction quand vous le souhaitez." },
                    ]);
                  }}
                  className="flex items-center justify-center gap-1.5 border border-neutral-200 text-neutral-600 text-sm font-medium px-4 py-2.5 rounded-xl hover:bg-neutral-50 transition-colors shrink-0"
                >
                  {lang === "ar" ? "إلغاء" : "Annuler"}
                </button>
              </div>
            )}

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

                {voiceSupported && (
                  <button
                    onClick={toggleVoice}
                    disabled={busy}
                    title={isListening ? "Arrêter l'écoute" : "Dicter un message"}
                    className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors shrink-0 ${
                      isListening
                        ? "bg-red-500 text-white animate-pulse"
                        : "text-neutral-400 hover:text-neutral-700 hover:bg-neutral-100 disabled:opacity-30"
                    }`}
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 1a3 3 0 013 3v8a3 3 0 01-6 0V4a3 3 0 013-3z"/>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 10a7 7 0 01-14 0"/>
                      <line x1="12" y1="19" x2="12" y2="23"/>
                      <line x1="8" y1="23" x2="16" y2="23"/>
                    </svg>
                  </button>
                )}

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
