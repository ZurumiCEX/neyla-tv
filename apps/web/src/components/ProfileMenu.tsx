"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { canAccessConsole, consoleHref } from "@/lib/admin-link";
import { useT } from "@/lib/i18n";
import { RoleBadge } from "@/components/RoleBadge";
import { Avatar } from "@/components/Avatar";

export function ProfileMenu() {
  const { user, logout, authFetch } = useAuth();
  const t = useT();
  const [open, setOpen] = useState(false);
  const [achCount, setAchCount] = useState(0);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  useEffect(() => {
    if (!user) return;
    authFetch<{ unlocked: number }>("/api/achievements")
      .then((d) => setAchCount(d.unlocked))
      .catch(() => setAchCount(0));
  }, [user, authFetch]);

  if (!user) return null;

  const adminHref = consoleHref(user);

  const items: { href: string; label: string }[] = [
    { href: `/u/${user.username}`, label: t("nav.myProfile") },
    { href: "/ma-chaine", label: t("nav.myChannel") },
    { href: "/dashboard", label: t("nav.dashboard") },
    { href: "/wallet", label: t("nav.wallet") },
    ...(user.is_streamer ? [{ href: "/dashboard/revenue", label: t("nav.revenue") }] : []),
    { href: "/abonnements", label: t("nav.subscriptions") },
    ...(user.is_streamer ? [] : [{ href: "/become-streamer", label: t("nav.becomeStreamer") }]),
    { href: "/invite", label: t("nav.invite") },
    { href: "/settings", label: t("nav.settings") },
    ...(canAccessConsole(user) ? [{ href: adminHref, label: t("nav.admin") }] : []),
  ];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={user.username}
        className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border border-neutral-700 hover:border-emerald-500"
      >
        <Avatar src={user.avatar_url} name={user.display_name || user.username} size={34} />
      </button>
      {achCount > 0 && (
        <span
          title={t("ach.count", { n: achCount })}
          className="pointer-events-none absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full border-2 border-neutral-950 bg-emerald-500 px-1 text-[9px] font-bold leading-none text-neutral-950"
        >
          {achCount > 99 ? "99+" : achCount}
        </span>
      )}

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-56 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 shadow-xl">
          <div className="flex items-center gap-2 border-b border-neutral-800 px-3 py-3 text-sm">
            <RoleBadge role={user.role} />
            <span className="truncate font-semibold text-neutral-100">@{user.username}</span>
          </div>
          <div className="py-1">
            {items.map((it) => (
              <Link
                key={it.href + it.label}
                href={it.href}
                onClick={() => setOpen(false)}
                className={`block px-3 py-2 text-sm hover:bg-neutral-800 ${
                  it.href === "/become-streamer"
                    ? "font-semibold text-secondary-light"
                    : "text-neutral-200"
                }`}
              >
                {it.label}
              </Link>
            ))}
          </div>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              logout();
            }}
            className="block w-full border-t border-neutral-800 px-3 py-2 text-left text-sm text-red-300 hover:bg-neutral-800"
          >
            {t("nav.logout")}
          </button>
        </div>
      )}
    </div>
  );
}
