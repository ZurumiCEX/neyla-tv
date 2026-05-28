"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

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
  heart: "M12 21s-7-4.35-9.5-8.5C1 9.5 2.5 6 6 6c2 0 3.2 1.2 4 2.5C10.8 7.2 12 6 14 6c3.5 0 5 3.5 3.5 6.5C19 16.65 12 21 12 21z",
  dashboard: "M4 4h7v7H4zM13 4h7v4h-7zM13 11h7v9h-7zM4 13h7v7H4z",
  wallet: "M3 7h18v12H3zM16 12h3M3 7l2-3h12l2 3",
  trophy: "M8 21h8M12 17v4M7 4h10v4a5 5 0 01-10 0zM7 6H4v2a3 3 0 003 3M17 6h3v2a3 3 0 01-3 3",
  inbox: "M4 5h16v14H4zM4 13h5l2 3h2l2-3h5",
  shield: "M12 3l8 3v5c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6z",
};

export function Sidebar() {
  const { user, loading, authFetch } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [follows, setFollows] = useState<FollowedChannel[]>([]);
  const pathname = usePathname();
  const t = useT();

  useEffect(() => {
    setCollapsed(localStorage.getItem("sidebar:collapsed") === "1");
  }, []);

  const toggle = useCallback(() => {
    setCollapsed((c) => {
      const next = !c;
      localStorage.setItem("sidebar:collapsed", next ? "1" : "0");
      return next;
    });
  }, []);

  useEffect(() => {
    if (loading || !user) {
      setFollows([]);
      return;
    }
    authFetch<{ results: FollowedChannel[] }>("/api/follows/me")
      .then((d) => setFollows([...d.results].sort((a, b) => Number(b.is_live) - Number(a.is_live))))
      .catch(() => setFollows([]));
  }, [loading, user, authFetch]);

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
            label: t("nav.follows"),
            icon: <Icon path={ICONS.heart} />,
            active: is("/suivis"),
          },
        ]
      : []),
  ];

  const space: NavItemDef[] = user
    ? [
        {
          href: "/dashboard",
          label: t("nav.dashboard"),
          icon: <Icon path={ICONS.dashboard} />,
          active: is("/dashboard"),
        },
        {
          href: "/wallet",
          label: t("nav.wallet"),
          icon: <Icon path={ICONS.wallet} />,
          active: is("/wallet"),
        },
        {
          href: "/achievements",
          label: t("nav.achievements"),
          icon: <Icon path={ICONS.trophy} />,
          active: is("/achievements"),
        },
        {
          href: "/inbox",
          label: t("nav.inbox"),
          icon: <Icon path={ICONS.inbox} />,
          active: is("/inbox"),
        },
      ]
    : [];

  const adminHref =
    user?.role === "moderator"
      ? "/admin/reports"
      : user?.role === "support"
        ? "/admin/messages"
        : "/admin/dashboard";
  const admin: NavItemDef[] =
    user && ["admin", "moderator", "support"].includes(user.role)
      ? [
          {
            href: adminHref,
            label: t("nav.admin"),
            icon: <Icon path={ICONS.shield} />,
            active: is("/admin"),
          },
        ]
      : [];

  const sections: { label: string; items: NavItemDef[] }[] = [
    { label: t("side.section.menu"), items: menu },
    { label: t("side.section.space"), items: space },
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
        aria-label={collapsed ? "Déplier" : "Replier"}
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
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
              {t("side.following")}
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
                    {c.streamer.avatar_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={c.streamer.avatar_url}
                        alt=""
                        className="h-7 w-7 rounded-full object-cover"
                      />
                    ) : (
                      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-neutral-800 text-xs text-neutral-400">
                        {(c.streamer.display_name || c.slug).charAt(0).toUpperCase()}
                      </span>
                    )}
                    {c.is_live && (
                      <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-neutral-950 bg-red-500" />
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
                      <span className="h-2 w-2 rounded-full bg-red-500" />
                      {typeof c.viewers === "number" && c.viewers > 0
                        ? c.viewers.toLocaleString("fr-FR")
                        : null}
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
        item.active
          ? "bg-emerald-500/10 text-emerald-300"
          : "text-neutral-300 hover:bg-neutral-900"
      } ${collapsed ? "justify-center px-2" : ""}`}
      title={item.label}
    >
      {item.icon}
      {!collapsed && <span>{item.label}</span>}
    </Link>
  );
}
