"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

type State = "loading" | "success" | "error";

function VerifyEmailContent() {
  const params = useSearchParams();
  const [state,   setState]   = useState<State>("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = params.get("token");
    if (!token) { setState("error"); setMessage("Lien invalide — aucun token trouvé."); return; }

    fetch(`/api/auth/verify-email?token=${encodeURIComponent(token)}`)
      .then(async r => {
        const data = await r.json().catch(() => ({}));
        if (r.ok) { setState("success"); setMessage(data.message ?? "Email vérifié !"); }
        else       { setState("error");   setMessage(data.detail  ?? "Lien invalide ou expiré."); }
      })
      .catch(() => { setState("error"); setMessage("Erreur réseau. Veuillez réessayer."); });
  }, [params]);

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-sm text-center">
        {state === "loading" && (
          <>
            <div className="w-14 h-14 rounded-full bg-neutral-100 flex items-center justify-center mx-auto mb-5">
              <svg className="w-6 h-6 text-neutral-400 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
            </div>
            <p className="text-sm text-neutral-500">Vérification en cours…</p>
          </>
        )}

        {state === "success" && (
          <>
            <div className="w-14 h-14 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center text-2xl mx-auto mb-5">✓</div>
            <h2 className="text-xl font-semibold text-neutral-900 mb-2">Email vérifié !</h2>
            <p className="text-sm text-neutral-500 mb-6">{message}</p>
            <Link href="/login" className="bg-black text-white text-sm font-medium px-6 py-2.5 rounded-xl hover:bg-neutral-800 transition-colors">
              Se connecter
            </Link>
          </>
        )}

        {state === "error" && (
          <>
            <div className="w-14 h-14 rounded-full bg-red-50 border border-red-100 flex items-center justify-center text-2xl mx-auto mb-5">✕</div>
            <h2 className="text-xl font-semibold text-neutral-900 mb-2">Lien invalide</h2>
            <p className="text-sm text-neutral-500 mb-6">{message}</p>
            <Link href="/forgot-password" className="text-sm font-medium text-neutral-900 underline underline-offset-2">
              Demander un nouveau lien
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailContent />
    </Suspense>
  );
}
