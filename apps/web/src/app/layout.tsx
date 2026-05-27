import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { I18nProvider } from "@/lib/i18n";
import { Navbar } from "@/components/Navbar";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Neyla TV",
  description: "Plateforme de streaming jeux vidéo (MVP)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="min-h-screen bg-neutral-950 text-neutral-100 antialiased">
        <I18nProvider>
          <AuthProvider>
            <Navbar />
            <div className="flex">
              <Sidebar />
              <div className="min-w-0 flex-1">{children}</div>
            </div>
          </AuthProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
