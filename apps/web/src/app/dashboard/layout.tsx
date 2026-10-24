"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  CalendarDays,
  ChartLine,
  Clapperboard,
  CircleDollarSign,
  ExternalLink,
  KeyRound,
  Radio,
  Trophy,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { DashboardProvider, useDashboard } from "@/components/dashboard/kit";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

const NAV: { href: string; key: string; icon: LucideIcon }[] = [
  { href: "/dashboard", key: "stream", icon: Radio },
  { href: "/dashboard/stream-key", key: "streamKey", icon: KeyRound },
  { href: "/dashboard/revenue", key: "revenue", icon: CircleDollarSign },
  { href: "/dashboard/achievements", key: "achievements", icon: Trophy },
  { href: "/dashboard/studio", key: "studio", icon: Clapperboard },
  { href: "/dashboard/analytics", key: "analytics", icon: ChartLine },
  { href: "/dashboard/moderation", key: "moderation", icon: Wrench },
  { href: "/dashboard/community", key: "community", icon: Users },
  { href: "/dashboard/events", key: "events", icon: CalendarDays },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const t = useT();
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;
  }
  return (
    <DashboardProvider>
      <div className="flex min-h-[calc(100vh-57px)] flex-col md:flex-row">
        <DashboardNav />
        <div className="min-w-0 flex-1">
          <DashboardHeader />
          <div className="p-3 sm:p-4">{children}</div>
        </div>
      </div>
    </DashboardProvider>
  );
}

function DashboardNav() {
  const t = useT();
  const pathname = usePathname() ?? "";
  return (
    <nav
      aria-label={t("dash2.navLabel")}
      className="flex shrink-0 gap-1 overflow-x-auto border-b border-neutral-800 bg-neutral-950 p-2 md:sticky md:top-0 md:h-[calc(100vh-57px)] md:w-60 md:flex-col md:overflow-visible md:border-b-0 md:border-r md:p-3"
    >
      {NAV.map(({ href, key, icon: Icon }) => {
        const active = href === "/dashboard" ? pathname === href : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`flex shrink-0 items-center gap-3 rounded-md px-3 py-2.5 text-[15px] font-semibold transition ${
              active
                ? "bg-neutral-800 text-neutral-50"
                : "text-neutral-300 hover:bg-neutral-900 hover:text-neutral-50"
            }`}
          >
            <Icon size={18} aria-hidden />
            <span className="whitespace-nowrap">{t(`dash2.nav.${key}`)}</span>
          </Link>
        );
      })}
    </nav>
  );
}

function DashboardHeader() {
  const t = useT();
  const { authFetch } = useAuth();
  const { channel, error, reload } = useDashboard();
  const [busy, setBusy] = useState(false);
  const [liveError, setLiveError] = useState<string | null>(null);

  async function toggleLive() {
    if (!channel) return;
    setBusy(true);
    setLiveError(null);
    try {
      await authFetch("/api/channels/me/live", {
        method: "POST",
        body: JSON.stringify({ live: !channel.is_live }),
      });
      await reload();
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setLiveError(e.data?.detail ?? t("dash2.liveError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {error && (
        <p className="m-3 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}
      {channel && !channel.is_provisioned && (
        <div className="m-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
          <p className="font-semibold text-amber-300">{t("dash.accessRequired")}</p>
          <p className="mt-1 text-sm text-neutral-300">{t("dash.accessDesc")}</p>
          <Link
            href="/become-streamer"
            className="mt-3 inline-block rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
          >
            {t("dash.makeRequest")}
          </Link>
        </div>
      )}
      {channel?.is_provisioned && (
        <div className="flex flex-wrap items-center justify-end gap-2 px-3 pt-3 sm:px-4">
          {liveError && <span className="mr-auto text-sm text-red-300">{liveError}</span>}
          <Link
            href={`/c/${channel.slug}`}
            className="flex h-9 items-center gap-1.5 rounded-md border border-neutral-700 px-3 text-sm font-semibold text-neutral-200 hover:border-neutral-500"
          >
            <ExternalLink size={15} aria-hidden />
            {t("dash.publicPage")}
          </Link>
          <button
            type="button"
            onClick={toggleLive}
            disabled={busy}
            className={`flex h-9 items-center gap-2 rounded-md px-4 text-sm font-bold disabled:opacity-50 ${
              channel.is_live
                ? "border border-red-500/60 text-red-300 hover:bg-red-500/10"
                : "bg-emerald-500 text-neutral-950 hover:bg-emerald-400"
            }`}
          >
            <Radio size={16} aria-hidden />
            {channel.is_live ? t("dash.endLive") : t("dash.goLive")}
          </button>
        </div>
      )}
    </>
  );
}
