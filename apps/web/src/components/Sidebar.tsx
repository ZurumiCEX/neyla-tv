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

function HomeIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 11l9-8 9 8M5 10v10h14V10" />
    </svg>
  );
}

function BrowseIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M15 9l-2 6-4 2 2-6z" />
    </svg>
  );
}

function HeartIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 21s-7-4.35-9.5-8.5C1 9.5 2.5 6 6 6c2 0 3.2 1.2 4 2.5C10.8 7.2 12 6 14 6c3.5 0 5 3.5 3.5 6.5C19 16.65 12 21 12 21z" />
    </svg>
  );
}

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
      .then((d) =>
        setFollows(
          [...d.results].sort((a, b) => Number(b.is_live) - Number(a.is_live)),
        ),
      )
      .catch(() => setFollows([]));
  }, [loading, user, authFetch]);

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

      <nav className="space-y-1">
        <NavItem href="/" label={t("side.home")} collapsed={collapsed} active={pathname === "/"}>
          <HomeIcon />
        </NavItem>
        <NavItem
          href="/parcourir"
          label={t("side.browse")}
          collapsed={collapsed}
          active={pathname?.startsWith("/parcourir") ?? false}
        >
          <BrowseIcon />
        </NavItem>
        {user && (
          <NavItem
            href="/suivis"
            label={t("nav.follows")}
            collapsed={collapsed}
            active={pathname?.startsWith("/suivis") ?? false}
          >
            <HeartIcon />
          </NavItem>
        )}
      </nav>

      {user && (
        <div className="mt-6">
          {!collapsed && (
            <p className="mb-2 px-2 text-xs uppercase tracking-wider text-neutral-500">
              {t("side.following")}
            </p>
          )}
          {follows.length === 0 ? (
            !collapsed && (
              <p className="px-2 text-xs text-neutral-600">{t("side.noFollows")}</p>
            )
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

function NavItem({
  href,
  label,
  collapsed,
  active,
  children,
}: {
  href: string;
  label: string;
  collapsed: boolean;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${
        active ? "bg-neutral-900 text-emerald-300" : "text-neutral-300 hover:bg-neutral-900"
      } ${collapsed ? "justify-center px-2" : ""}`}
      title={label}
    >
      {children}
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}
