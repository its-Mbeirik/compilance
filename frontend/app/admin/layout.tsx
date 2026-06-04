"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../contexts/auth";

const NAV = [
  { href: "/admin",         label: "Tableau de bord" },
  { href: "/admin/pending", label: "Approbations"    },
  { href: "/admin/users",   label: "Utilisateurs"    },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user)                 { router.replace("/login"); return; }
    if (user.role !== "admin") { router.replace("/");      return; }
  }, [user, loading, router]);

  if (loading || !user || user.role !== "admin") return null;

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-[#111] flex flex-col shrink-0 h-full">
        <div className="px-4 py-5 border-b border-white/10 flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-white flex items-center justify-center text-black text-xs font-bold shrink-0">
            ⚖
          </div>
          <div>
            <p className="text-white text-sm font-semibold leading-none">ConformIA</p>
            <p className="text-white/40 text-[10px] mt-0.5">Administration</p>
          </div>
        </div>

        <nav className="flex-1 px-2 py-4 space-y-0.5">
          {NAV.map(l => (
            <Link
              key={l.href}
              href={l.href}
              className="block text-white/60 hover:bg-white/10 hover:text-white text-sm px-3 py-2.5 rounded-lg transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-white/10">
          <p className="text-white/40 text-xs truncate mb-1">{user.name}</p>
          <div className="text-[10px] bg-white/10 text-white/60 px-2 py-0.5 rounded-full w-fit mb-3">
            Admin
          </div>
          <button
            onClick={logout}
            className="text-xs text-white/40 hover:text-white transition-colors"
          >
            Déconnexion
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-8">
        {children}
      </main>
    </div>
  );
}
