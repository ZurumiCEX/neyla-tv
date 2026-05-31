"use client";

import { usePathname } from "next/navigation";
import { AnnouncementBar } from "@/components/AnnouncementBar";
import { Footer } from "@/components/Footer";
import { Navbar } from "@/components/Navbar";
import { Sidebar } from "@/components/Sidebar";

/** Masque la navigation globale sur les routes overlay (browser source OBS). */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname?.startsWith("/overlay")) return <>{children}</>;
  return (
    <>
      <Navbar />
      <AnnouncementBar />
      <div className="flex">
        <Sidebar />
        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <div className="flex-1">{children}</div>
          <Footer />
        </div>
      </div>
    </>
  );
}
