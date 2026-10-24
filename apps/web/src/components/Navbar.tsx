"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { AuraBalance } from "@/components/AuraBalance";
import { EventsMenu } from "@/components/EventsMenu";
import { GuidesMenu } from "@/components/GuidesMenu";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { NotificationBell } from "@/components/NotificationBell";
import { ProfileMenu } from "@/components/ProfileMenu";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Menu, Search } from "lucide-react";

export function Navbar() {
  const { user, loading } = useAuth();
  const t = useT();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  function submitSearch(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = search.trim();
    if (!trimmed) return;
    setMenuOpen(false);
    router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  return (
    <nav className="relative z-50 border-b border-neutral-800 bg-neutral-950/90 backdrop-blur">
      <div className="flex w-full items-center gap-3 px-4 py-2.5 sm:gap-4">
        {/* Gauche : burger (mobile) + logo */}
        <div className="flex shrink-0 items-center gap-3 sm:gap-4">
          <button
            type="button"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label={t("nav.menu")}
            aria-expanded={menuOpen}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-neutral-300 hover:bg-neutral-800 sm:hidden"
          >
            <BurgerIcon />
          </button>
          <Link href="/" className="text-lg font-bold tracking-tight">
            Neyla<span className="text-emerald-400">.tv</span>
          </Link>
        </div>

        {/* Centre : barre de recherche (masquée sur très petit écran) */}
        <div className="hidden flex-1 justify-center sm:flex">
          <form onSubmit={submitSearch} className="w-full max-w-md">
            <div className="relative">
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("nav.search")}
                className="w-full rounded-full border border-neutral-800 bg-neutral-900 px-4 py-1.5 pr-10 text-sm text-neutral-100 outline-none focus:border-secondary-light"
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

        <div className="flex-1 sm:hidden" />

        {/* Droite : contrôles */}
        <div className="flex shrink-0 items-center gap-2 text-sm">
          {/* Guides et langue : masqués sur mobile pour éviter le défilement horizontal. */}
          <div className="hidden items-center gap-2 sm:flex">
            <GuidesMenu />
          </div>
          <ThemeToggle />
          <div className="hidden items-center sm:flex">
            <LanguageSwitcher />
          </div>

          {loading ? (
            <span className="px-2 text-neutral-500">…</span>
          ) : user ? (
            <>
              <AuraBalance />
              <div className="hidden items-center sm:flex">
                <EventsMenu />
              </div>
              <NotificationBell />
              <span className="hidden text-sm text-neutral-400 lg:inline">@{user.username}</span>
              <ProfileMenu />
            </>
          ) : (
            <>
              <div className="hidden items-center sm:flex">
                <EventsMenu />
              </div>
              <Link
                href="/login"
                className="hidden text-neutral-300 hover:text-emerald-300 sm:inline"
              >
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

      {/* Panneau mobile */}
      {menuOpen && (
        <div className="border-t border-neutral-800 px-4 py-3 sm:hidden">
          <form onSubmit={submitSearch} className="mb-3">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t("nav.search")}
              className="w-full rounded-full border border-neutral-800 bg-neutral-900 px-4 py-1.5 text-sm text-neutral-100 outline-none focus:border-secondary-light"
            />
          </form>
          {[
            { href: "/", label: t("side.home"), show: true },
            { href: "/parcourir", label: t("side.browse"), show: true },
            { href: "/suivis", label: t("side.follows"), show: Boolean(user) },
            { href: "/instant", label: t("side.shorts"), show: true },
          ]
            .filter((l) => l.show)
            .map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setMenuOpen(false)}
                className="block rounded-lg px-2 py-2 text-sm text-neutral-200 hover:bg-neutral-800"
              >
                {l.label}
              </Link>
            ))}
          {!user && (
            <div className="mt-2 flex gap-2">
              <Link
                href="/login"
                onClick={() => setMenuOpen(false)}
                className="flex-1 rounded-lg border border-neutral-700 px-3 py-2 text-center text-sm text-neutral-200"
              >
                {t("nav.login")}
              </Link>
              <Link
                href="/register"
                onClick={() => setMenuOpen(false)}
                className="flex-1 rounded-lg bg-emerald-500 px-3 py-2 text-center text-sm font-semibold text-neutral-950"
              >
                {t("nav.register")}
              </Link>
            </div>
          )}
          <div className="mt-3 flex items-center gap-2 border-t border-neutral-800 pt-3">
            <LanguageSwitcher />
            <GuidesMenu />
            <EventsMenu />
          </div>
        </div>
      )}
    </nav>
  );
}

function SearchIcon() {
  return <Search size={16} aria-hidden />;
}

function BurgerIcon() {
  return <Menu size={20} aria-hidden />;
}
