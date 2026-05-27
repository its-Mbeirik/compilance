const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Finding = {
  id: string;
  severity: "CRITIQUE" | "MAJEURE" | "MINEURE";
  category: string;
  clause_ref: string | null;
  description: string;
  recommendation: string | null;
  legal_basis: Array<{ source: string; article: string | null; excerpt: string }>;
  confidence: number;
};

export type Contract = {
  id: string;
  filename: string;
  contract_type: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  findings: Finding[];
  report: string | null;
};

export async function uploadContract(file: File, contractType: string): Promise<Contract> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("contract_type", contractType);
  const res = await fetch(`${API_URL}/contracts/verify`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Upload failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function getContract(id: string): Promise<Contract> {
  const res = await fetch(`${API_URL}/contracts/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
  return res.json();
}

export async function listContracts(): Promise<Contract[]> {
  const res = await fetch(`${API_URL}/contracts/`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
  return res.json();
}

export type ChatMessage = { role: "user" | "assistant"; content: string };

export type ChatSource = {
  source: string;
  article: string | null;
  excerpt: string;
  score: number;
};

export type ChatResponse = {
  reply: string;
  sources: ChatSource[];
  contract_context: { filename: string; contract_type: string; status: string } | null;
};

export async function sendChat(
  messages: ChatMessage[],
  opts?: { contractId?: string | null; k?: number },
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      contract_id: opts?.contractId ?? null,
      k: opts?.k ?? 5,
    }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status} ${await res.text()}`);
  return res.json();
}

export function downloadReportUrl(contractId: string, format: "md" | "docx" = "docx") {
  return `${API_URL}/contracts/${contractId}/download?format=${format}`;
}

export async function generateCorrected(contractId: string, format: "md" | "docx" = "docx"): Promise<Blob> {
  const res = await fetch(`${API_URL}/contracts/${contractId}/corrected?format=${format}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Correction failed: ${res.status} ${await res.text()}`);
  return res.blob();
}

export function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}
