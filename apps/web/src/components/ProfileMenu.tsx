"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { RoleBadge } from "@/components/RoleBadge";

export function ProfileMenu() {
  const { user, logout } = useAuth();
  const t = useT();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  if (!user) return null;

  const initial = (user.display_name || user.username || "?").charAt(0).toUpperCase();
  const adminHref =
    user.role === "moderator"
      ? "/console/reports"
      : user.role === "support"
        ? "/console/messages"
        : "/console/dashboard";

  const items: { href: string; label: string }[] = [
    { href: "/ma-chaine", label: t("nav.myChannel") },
    { href: "/dashboard", label: t("nav.dashboard") },
    { href: "/wallet", label: t("nav.wallet") },
    ...(user.is_streamer ? [{ href: "/revenus", label: t("nav.revenue") }] : []),
    { href: "/abonnements", label: t("nav.subscriptions") },
    ...(user.is_streamer ? [] : [{ href: "/become-streamer", label: t("nav.becomeStreamer") }]),
    { href: "/invite", label: t("nav.invite") },
    { href: "/settings", label: t("nav.settings") },
    ...(["admin", "moderator", "support"].includes(user.role) || user.is_staff
      ? [{ href: adminHref, label: t("nav.admin") }]
      : []),
  ];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={user.username}
        className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border border-neutral-700 bg-neutral-800 text-sm font-semibold text-neutral-100 hover:border-emerald-500"
      >
        {user.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.avatar_url} alt="" className="h-full w-full object-cover" />
        ) : (
          initial
        )}
      </button>

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
