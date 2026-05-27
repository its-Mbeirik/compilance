import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { IconHistory, IconMessage, IconScale } from "@/components/icons";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });

export const metadata: Metadata = {
  title: "Conformité — Assistant juridique",
  description: "Vérification de conformité contractuelle aux lois mauritaniennes.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={inter.variable}>
      <body className="min-h-screen flex flex-col">
        <header className="border-b border-neutral-200 bg-white">
          <div className="mx-auto max-w-7xl px-6 h-14 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2.5 group">
              <span className="inline-flex h-7 w-7 items-center justify-center rounded border border-neutral-200 bg-neutral-50 text-neutral-700">
                <IconScale size={15} />
              </span>
              <span className="text-[15px] font-medium text-neutral-900 tracking-tight">
                Conformité
              </span>
              <span className="text-xs text-neutral-400 ml-1 hidden sm:inline">
                / Assistant juridique mauritanien
              </span>
            </a>

            <nav className="flex gap-1 items-center text-sm">
              <NavLink href="/" label="Assistant" icon={<IconMessage size={15} />} />
              <NavLink href="/contracts" label="Historique" icon={<IconHistory size={15} />} />
            </nav>
          </div>
        </header>

        <main className="flex-1 mx-auto w-full max-w-7xl px-6 py-5">{children}</main>
      </body>
    </html>
  );
}

function NavLink({ href, label, icon }: { href: string; label: string; icon: React.ReactNode }) {
  return (
    <a
      href={href}
      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 transition-colors"
    >
      {icon}
      <span>{label}</span>
    </a>
  );
}
