"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../contexts/auth";

export default function PendingPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user)                        { router.replace("/login"); return; }
    if (user.role === "admin")        { router.replace("/admin"); return; }
    if (user.status === "approved")   { router.replace("/");      return; }
  }, [user, loading, router]);

  if (loading || !user) return null;

  const rejected = user.status === "rejected";

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        <div className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl mx-auto mb-5 ${
          rejected
            ? "bg-red-50 border border-red-100"
            : "bg-amber-50 border border-amber-100"
        }`}>
          {rejected ? "✕" : "⏳"}
        </div>

        {rejected ? (
          <>
            <h2 className="text-xl font-semibold text-neutral-900 mb-2">Compte refusé</h2>
            <p className="text-sm text-neutral-500 mb-6">
              Votre demande d&apos;accès a été refusée par l&apos;administrateur.
              Contactez le support si vous pensez qu&apos;il s&apos;agit d&apos;une erreur.
            </p>
          </>
        ) : (
          <>
            <h2 className="text-xl font-semibold text-neutral-900 mb-2">Compte en attente</h2>
            <p className="text-sm text-neutral-500 mb-2">
              Bonjour <strong>{user.name}</strong>,
            </p>
            <p className="text-sm text-neutral-500 mb-6">
              Votre compte est en cours d&apos;examen par un administrateur.
              Vous pourrez vous connecter dès qu&apos;il sera approuvé.
            </p>
          </>
        )}

        <button
          onClick={logout}
          className="text-sm text-neutral-400 hover:text-neutral-700 transition-colors underline underline-offset-2"
        >
          Se déconnecter
        </button>
      </div>
    </div>
  );
}
