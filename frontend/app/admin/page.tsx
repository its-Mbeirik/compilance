"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useApiFetch } from "../contexts/auth";

interface Stats {
  pending:          number;
  total_users:      number;
  total_sub_users:  number;
}

export default function AdminDashboard() {
  const apiFetch = useApiFetch();
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    apiFetch("/api/admin/stats")
      .then(r => r.ok ? r.json() : null)
      .then(d => d && setStats(d))
      .catch(() => {});
  }, [apiFetch]);

  const cards = [
    {
      label: "En attente d'approbation",
      value: stats?.pending ?? "—",
      bg: "bg-amber-50 border-amber-100",
      text: "text-amber-700",
      href: "/admin/pending",
    },
    {
      label: "Utilisateurs validés",
      value: stats?.total_users ?? "—",
      bg: "bg-emerald-50 border-emerald-100",
      text: "text-emerald-700",
      href: "/admin/users",
    },
    {
      label: "Sous-utilisateurs",
      value: stats?.total_sub_users ?? "—",
      bg: "bg-neutral-50 border-neutral-200",
      text: "text-neutral-700",
      href: "/admin/users",
    },
  ];

  return (
    <div>
      <h1 className="text-xl font-semibold text-neutral-900 mb-1">Tableau de bord</h1>
      <p className="text-sm text-neutral-400 mb-8">Vue d&apos;ensemble de la plateforme</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        {cards.map(c => (
          <Link
            key={c.label}
            href={c.href}
            className={`block rounded-xl border p-5 ${c.bg} hover:shadow-sm transition-shadow`}
          >
            <p className={`text-3xl font-bold mb-1 ${c.text}`}>{c.value}</p>
            <p className="text-xs text-neutral-500">{c.label}</p>
          </Link>
        ))}
      </div>

      <div className="flex gap-3">
        <Link
          href="/admin/pending"
          className="bg-black text-white text-sm font-medium px-4 py-2.5 rounded-lg hover:bg-neutral-800 transition-colors"
        >
          Voir les approbations en attente →
        </Link>
        <Link
          href="/admin/users"
          className="border border-neutral-200 text-neutral-700 text-sm font-medium px-4 py-2.5 rounded-lg hover:bg-neutral-50 transition-colors"
        >
          Gérer les utilisateurs →
        </Link>
      </div>
    </div>
  );
}
