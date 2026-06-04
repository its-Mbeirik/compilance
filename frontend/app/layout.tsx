import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "./contexts/auth";

export const metadata: Metadata = {
  title: "ConformIA — Assistant de conformité contractuelle",
  description: "Vérification automatique Code du Travail mauritanien & COC",
  icons: { icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚖️</text></svg>" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="bg-white overflow-hidden">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
