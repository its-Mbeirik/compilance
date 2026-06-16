"use client";
import Link from "next/link";
import { useAuth, AuthUser } from "../contexts/auth";

const ROLE_LABEL: Record<string, string> = {
  user:     "Utilisateur",
  sub_user: "Assistant",
};

function navLinks(user: AuthUser) {
  const links = [{ href: "/", label: "Chat juridique" }];
  if (user.role === "user") links.push({ href: "/sub-users", label: "Assistants" });
  links.push({ href: "/settings", label: "Paramètres" });
  return links;
}

export default function UserSidebar() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <aside className="w-56 bg-[#111] flex flex-col shrink-0 h-full">
      <div className="px-4 py-5 border-b border-white/10 flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-full bg-white flex items-center justify-center text-black text-xs font-bold shrink-0">
          ⚖
        </div>
        <p className="text-white text-sm font-semibold">ConformIA</p>
      </div>

      <nav className="flex-1 px-2 py-4 space-y-0.5">
        {navLinks(user).map(l => (
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
        <div className="text-[10px] bg-white/10 text-white/50 px-2 py-0.5 rounded-full w-fit mb-3">
          {ROLE_LABEL[user.role] ?? user.role}
        </div>
        <button
          onClick={logout}
          className="text-xs text-white/40 hover:text-white transition-colors"
        >
          Déconnexion
        </button>
      </div>
    </aside>
  );
}
