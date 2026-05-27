"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { NotificationBell } from "@/components/NotificationBell";
import { RoleBadge } from "@/components/RoleBadge";

export function Navbar() {
  const { user, loading, logout } = useAuth();
  const t = useT();
  const router = useRouter();
  const [search, setSearch] = useState("");

  function submitSearch(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = search.trim();
    if (!trimmed) return;
    router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  return (
    <nav className="border-b border-neutral-800 bg-neutral-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        {/* Gauche : logo (position fixe) */}
        <div className="flex shrink-0 items-center gap-4">
          <Link href="/" className="text-lg font-bold tracking-tight">
            Neyla<span className="text-emerald-400">.tv</span>
          </Link>
          <Link
            href="/parcourir"
            className="text-sm text-neutral-300 hover:text-emerald-300 md:hidden"
          >
            {t("nav.browse")}
          </Link>
        </div>

        {/* Droite : barre de recherche + liens */}
        <div className="flex items-center gap-3 text-sm">
          <form onSubmit={submitSearch} className="hidden md:block">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("nav.search")}
              className="w-56 rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-sm text-neutral-100 outline-none focus:border-emerald-500 lg:w-72"
            />
          </form>

          <LanguageSwitcher />

          {loading ? (
            <span className="text-neutral-500">…</span>
          ) : user ? (
            <>
              {(user.is_staff || user.role === "admin") && (
                <Link
                  href="/admin/analytics"
                  className="hidden text-amber-300 hover:text-amber-200 lg:inline"
                >
                  {t("nav.admin")}
                </Link>
              )}
              {!user.is_streamer && (
                <Link
                  href="/become-streamer"
                  className="hidden text-neutral-300 hover:text-emerald-300 lg:inline"
                >
                  {t("nav.becomeStreamer")}
                </Link>
              )}
              <Link href="/dashboard" className="text-neutral-300 hover:text-emerald-300">
                {t("nav.dashboard")}
              </Link>
              <Link
                href={`/c/${user.username}`}
                className="text-neutral-300 hover:text-emerald-300"
              >
                {t("nav.myChannel")}
              </Link>
              <Link
                href="/wallet"
                className="hidden text-amber-300 hover:text-amber-200 sm:inline"
              >
                {t("nav.aura")}
              </Link>
              <Link
                href="/settings"
                className="hidden text-neutral-300 hover:text-emerald-300 sm:inline"
              >
                {t("nav.settings")}
              </Link>
              <NotificationBell />
              <span className="hidden items-center text-neutral-500 sm:inline-flex">
                <RoleBadge role={user.role} />@{user.username}
              </span>
              <button
                type="button"
                onClick={() => logout()}
                className="rounded-md border border-neutral-700 px-2 py-1 text-neutral-300 hover:border-neutral-500"
              >
                {t("nav.logout")}
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-neutral-300 hover:text-emerald-300">
                {t("nav.login")}
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-emerald-500 px-3 py-1 font-semibold text-neutral-950 hover:bg-emerald-400"
              >
                {t("nav.register")}
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
