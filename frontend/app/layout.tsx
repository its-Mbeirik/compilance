import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Assistant Conformité | OHADA & Code du Travail MR",
  description: "Vérification automatique de conformité contractuelle",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="bg-gray-50 min-h-screen">
        <nav className="bg-blue-800 text-white px-6 py-3 flex items-center gap-6 shadow">
          <a href="/" className="font-bold text-lg tracking-tight">
            ⚖ ConformIA
          </a>
          <a href="/upload" className="text-blue-200 hover:text-white text-sm">
            Nouvelle analyse
          </a>
          <a href="/analyses" className="text-blue-200 hover:text-white text-sm">
            Mes analyses
          </a>
        </nav>
        <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
