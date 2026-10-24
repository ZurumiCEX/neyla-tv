"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { canAccessConsole, consoleHref } from "@/lib/admin-link";
import { onFollowsChanged } from "@/lib/follow-events";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";
import { Avatar } from "@/components/Avatar";

type FollowedChannel = {
  slug: string;
  is_live: boolean;
  viewers?: number;
  streamer: { display_name: string; avatar_url: string };
  category: { name: string } | null;
};

type NavItemDef = { href: string; label: string; icon: React.ReactNode; active: boolean };

function Icon({ path, fill = false }: { path: string; fill?: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className="h-5 w-5 shrink-0"
      fill={fill ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={path} />
    </svg>
  );
}

const ICONS = {
  home: "M3 11l9-8 9 8M5 10v10h14V10",
  browse: "M12 3a9 9 0 100 18 9 9 0 000-18zM15 9l-2 6-4 2 2-6z",
  heart:
    "M12 21s-7-4.35-9.5-8.5C1 9.5 2.5 6 6 6c2 0 3.2 1.2 4 2.5C10.8 7.2 12 6 14 6c3.5 0 5 3.5 3.5 6.5C19 16.65 12 21 12 21z",
  // Écran vertical + éclair : vidéos courtes « Instant ».
  shorts: "M7 2h10a2 2 0 012 2v16a2 2 0 01-2 2H7a2 2 0 01-2-2V4a2 2 0 012-2zM13 7l-3 5h4l-3 5",
  shield: "M12 3l8 3v5c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6z",
};

export function Sidebar() {
  const { user, loading, authFetch } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [follows, setFollows] = useState<FollowedChannel[]>([]);
  const pathname = usePathname();
  const t = useT();
  const { num } = useFormat();

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem("sidebar:collapsed") === "1");
    } catch {
      /* stockage indisponible */
    }
  }, []);

  const toggle = useCallback(() => {
    setCollapsed((c) => {
      const next = !c;
      try {
        localStorage.setItem("sidebar:collapsed", next ? "1" : "0");
      } catch {
        /* stockage indisponible */
      }
      return next;
    });
  }, []);

  const loadFollows = useCallback(() => {
    authFetch<{ results: FollowedChannel[] }>("/api/follows/me")
      .then((d) => setFollows([...d.results].sort((a, b) => Number(b.is_live) - Number(a.is_live))))
      .catch(() => setFollows([]));
  }, [authFetch]);

  // Rafraîchi au follow/unfollow et toutes les 60 s (une chaîne peut passer live).
  useEffect(() => {
    if (loading || !user) {
      setFollows([]);
      return;
    }
    loadFollows();
    const off = onFollowsChanged(loadFollows);
    const id = setInterval(loadFollows, 60_000);
    return () => {
      off();
      clearInterval(id);
    };
  }, [loading, user, loadFollows]);

  const is = (p: string, exact = false) =>
    exact ? pathname === p : (pathname?.startsWith(p) ?? false);

  const menu: NavItemDef[] = [
    { href: "/", label: t("side.home"), icon: <Icon path={ICONS.home} />, active: is("/", true) },
    {
      href: "/parcourir",
      label: t("side.browse"),
      icon: <Icon path={ICONS.browse} />,
      active: is("/parcourir"),
    },
    ...(user
      ? [
          {
            href: "/suivis",
            label: t("side.follows"),
            icon: <Icon path={ICONS.heart} />,
            active: is("/suivis"),
          },
        ]
      : []),
    {
      href: "/instant",
      label: t("side.shorts"),
      icon: <Icon path={ICONS.shorts} />,
      active: is("/instant"),
    },
  ];

  const adminHref = consoleHref(user);
  const admin: NavItemDef[] = canAccessConsole(user)
    ? [
        {
          href: adminHref,
          label: t("nav.admin"),
          icon: <Icon path={ICONS.shield} />,
          active: is("/console"),
        },
      ]
    : [];

  const sections: { label: string; items: NavItemDef[] }[] = [
    { label: t("side.section.menu"), items: menu },
    { label: t("side.section.admin"), items: admin },
  ];

  return (
    <aside
      className={`${collapsed ? "w-16" : "w-60"} sticky top-0 hidden h-screen shrink-0 overflow-y-auto border-r border-neutral-800 bg-neutral-950 px-2 py-4 md:block`}
    >
      <button
        type="button"
        onClick={toggle}
        className="mb-3 flex w-full items-center justify-center rounded-lg px-2 py-2 text-neutral-400 hover:bg-neutral-900 hover:text-neutral-100"
        aria-label={collapsed ? t("side.expand") : t("side.collapse")}
        title={collapsed ? t("side.expand") : t("side.collapse")}
      >
        <svg
          viewBox="0 0 24 24"
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          {collapsed ? <path d="M9 6l6 6-6 6" /> : <path d="M15 6l-6 6 6 6" />}
        </svg>
      </button>

      {sections.map((section) =>
        section.items.length === 0 ? null : (
          <nav key={section.label} className="mb-4 space-y-1">
            {!collapsed && (
              <p className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-neutral-600">
                {section.label}
              </p>
            )}
            {section.items.map((item) => (
              <NavItem key={item.href} item={item} collapsed={collapsed} />
            ))}
          </nav>
        ),
      )}

      {user && (
        <div className="mt-2 border-t border-neutral-800/60 pt-4">
          {!collapsed && (
            <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-neutral-600">
              {t("side.followedChannels")}
            </p>
          )}
          {follows.length === 0 ? (
            !collapsed && <p className="px-3 text-xs text-neutral-600">{t("side.noFollows")}</p>
          ) : (
            <div className="space-y-1">
              {follows.map((c) => (
                <Link
                  key={c.slug}
                  href={`/c/${c.slug}`}
                  className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-neutral-900"
                  title={c.streamer.display_name || c.slug}
                >
                  <span className="relative shrink-0">
                    <Avatar
                      src={c.streamer.avatar_url}
                      name={c.streamer.display_name || c.slug}
                      size={28}
                    />
                    {c.is_live && (
                      <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-[1px] border-2 border-neutral-950 bg-secondary" />
                    )}
                  </span>
                  {!collapsed && (
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm text-neutral-200">
                        {c.streamer.display_name || c.slug}
                      </span>
                      {c.is_live && c.category && (
                        <span className="block truncate text-xs text-neutral-500">
                          {c.category.name}
                        </span>
                      )}
                    </span>
                  )}
                  {!collapsed && c.is_live && (
                    <span className="flex shrink-0 items-center gap-1 self-start pt-0.5 text-xs text-neutral-400">
                      <span className="h-2 w-2 rounded-[1px] bg-secondary" />
                      {typeof c.viewers === "number" && c.viewers > 0 ? num(c.viewers) : null}
                    </span>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </aside>
  );
}

function NavItem({ item, collapsed }: { item: NavItemDef; collapsed: boolean }) {
  return (
    <Link
      href={item.href}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
        item.active ? "bg-emerald-500/10 text-emerald-300" : "text-neutral-300 hover:bg-neutral-900"
      } ${collapsed ? "justify-center px-2" : ""}`}
      title={item.label}
    >
      {item.icon}
      {!collapsed && <span>{item.label}</span>}
    </Link>
  );
}
