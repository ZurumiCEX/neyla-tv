"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { NotificationBell } from "@/components/NotificationBell";
import { ProfileMenu } from "@/components/ProfileMenu";

export function Navbar() {
  const { user, loading } = useAuth();
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
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-2.5">
        {/* Gauche : logo + navigation */}
        <div className="flex shrink-0 items-center gap-4">
          <Link href="/" className="text-lg font-bold tracking-tight">
            Neyla<span className="text-emerald-400">.tv</span>
          </Link>
          <Link
            href="/parcourir"
            className="hidden text-sm text-neutral-300 hover:text-emerald-300 sm:inline"
          >
            {t("nav.browse")}
          </Link>
        </div>

        {/* Centre : barre de recherche */}
        <div className="flex flex-1 justify-center">
          <form onSubmit={submitSearch} className="w-full max-w-md">
            <div className="relative">
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("nav.search")}
                className="w-full rounded-full border border-neutral-800 bg-neutral-900 px-4 py-1.5 pr-10 text-sm text-neutral-100 outline-none focus:border-emerald-500"
              />
              <button
                type="submit"
                aria-label={t("nav.search")}
                className="absolute right-1 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full text-neutral-400 hover:text-neutral-100"
              >
                <SearchIcon />
              </button>
            </div>
          </form>
        </div>

        {/* Droite : contrôles */}
        <div className="flex shrink-0 items-center gap-2 text-sm">
          <LanguageSwitcher />

          {loading ? (
            <span className="px-2 text-neutral-500">…</span>
          ) : user ? (
            <>
              <Link
                href="/wallet"
                aria-label={t("nav.aura")}
                title={t("nav.aura")}
                className="flex h-9 items-center gap-1 rounded-full px-2 text-amber-300 hover:bg-neutral-800"
              >
                <AuraIcon />
                <span className="hidden text-xs font-semibold sm:inline">{t("nav.aura")}</span>
              </Link>

              <NotificationBell />

              <span className="hidden text-sm text-neutral-400 lg:inline">@{user.username}</span>

              <ProfileMenu />
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

function SearchIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

function AuraIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
    </svg>
  );
}
