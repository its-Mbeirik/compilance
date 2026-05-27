"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";

export default function UploadPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [jurisdiction, setJurisdiction] = useState<"ohada" | "mauritania_labor">("ohada");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return setError("Veuillez sélectionner un fichier.");
    setError("");
    setLoading(true);

    const form = new FormData();
    form.append("file", file);
    form.append("jurisdiction", jurisdiction);

    try {
      const res = await fetch("/api/analyses", { method: "POST", body: form });
      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.detail || "Erreur serveur");
      }
      const data = await res.json();
      router.push(`/analyses/${data.analysis_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-12">
      <h1 className="text-2xl font-bold text-blue-800 mb-2">Nouvelle analyse de conformité</h1>
      <p className="text-gray-500 mb-8 text-sm">
        Déposez votre contrat (PDF, DOCX ou TXT) — le système vérifie automatiquement
        sa conformité aux réglementations OHADA ou du Code du Travail mauritanien.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition
            ${dragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400 bg-white"}`}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <p className="text-blue-700 font-medium">📄 {file.name}</p>
          ) : (
            <>
              <p className="text-gray-400 text-3xl mb-2">☁</p>
              <p className="text-gray-500 text-sm">
                Glissez votre fichier ici ou <span className="text-blue-600 underline">parcourir</span>
              </p>
              <p className="text-gray-400 text-xs mt-1">PDF, DOCX, TXT — max 10 MB</p>
            </>
          )}
        </div>

        {/* Juridiction */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Juridiction</label>
          <div className="flex gap-4">
            {(["ohada", "mauritania_labor"] as const).map((j) => (
              <label key={j} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="jurisdiction"
                  value={j}
                  checked={jurisdiction === j}
                  onChange={() => setJurisdiction(j)}
                  className="accent-blue-700"
                />
                <span className="text-sm text-gray-700">
                  {j === "ohada" ? "OHADA — Droit des sociétés" : "Code du Travail Mauritanien"}
                </span>
              </label>
            ))}
          </div>
        </div>

        {error && <p className="text-red-600 text-sm bg-red-50 rounded p-3">{error}</p>}

        <button
          type="submit"
          disabled={loading || !file}
          className="w-full bg-blue-700 hover:bg-blue-800 disabled:bg-gray-300
                     text-white font-semibold py-3 rounded-xl transition"
        >
          {loading ? "Envoi en cours…" : "Lancer l'analyse"}
        </button>
      </form>
    </div>
  );
}
