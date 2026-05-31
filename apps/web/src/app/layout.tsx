import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { I18nProvider } from "@/lib/i18n";
import { GuideProgressProvider } from "@/lib/use-guide-progress";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Neyla TV",
  description: "Plateforme de streaming jeux vidéo (MVP)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <head>
        {/* Évite le FOUC : applique le thème stocké avant l'hydratation React. */}
        <script
          dangerouslySetInnerHTML={{
            __html:
              "try{var t=localStorage.getItem('neyla:theme');document.documentElement.setAttribute('data-theme',t==='light'?'light':'dark');}catch(_){document.documentElement.setAttribute('data-theme','dark');}",
          }}
        />
      </head>
      <body className="min-h-screen bg-neutral-950 text-neutral-100 antialiased">
        <I18nProvider>
          <AuthProvider>
            <GuideProgressProvider>
              <AppShell>{children}</AppShell>
            </GuideProgressProvider>
          </AuthProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
