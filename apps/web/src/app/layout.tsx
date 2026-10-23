import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { I18nProvider } from "@/lib/i18n";
import { GuideProgressProvider } from "@/lib/use-guide-progress";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Neyla TV",
  description:
    "Neyla TV — streaming en direct et vidéos Instant pour les créateurs d'Afrique de l'Ouest francophone. Soutiens tes streamers en Aura.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // Le script de <head> ajuste data-theme / lang avant hydratation.
    <html lang="fr" suppressHydrationWarning>
      <head>
        {/* Évite le FOUC : applique le thème stocké avant l'hydratation React. */}
        <script
          dangerouslySetInnerHTML={{
            __html:
              "try{var t=localStorage.getItem('neyla:theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'}document.documentElement.setAttribute('data-theme',t);var l=localStorage.getItem('locale');if(l)document.documentElement.lang=l;}catch(_){document.documentElement.setAttribute('data-theme','dark');}",
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
