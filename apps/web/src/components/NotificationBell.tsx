"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type TFn = (key: string, params?: Record<string, string | number>) => string;

type Notif = {
  id: number;
  type: string;
  payload: Record<string, string>;
  read_at: string | null;
  created_at: string;
};

const POLL_MS = 20_000;

function describe(n: Notif, t: TFn): { text: string; href?: string } {
  const name = n.payload.display_name || n.payload.username || n.payload.slug || "";
  const user = n.payload.username ?? "";
  switch (n.type) {
    case "live_started":
      return { text: t("notif.live", { name }), href: `/c/${n.payload.slug}` };
    case "new_follower":
      return { text: t("notif.follower", { user }) };
    case "subscription":
      return n.payload.gifted
        ? {
            text: t("notif.gifted", {
              user: n.payload.gifter ?? "",
              channel: n.payload.channel ?? "",
            }),
          }
        : { text: t("notif.subscription", { user }) };
    case "tip_received":
      return {
        text: t("notif.tip", { user, n: n.payload.aura ?? "" }),
        href: n.payload.slug ? `/c/${n.payload.slug}` : undefined,
      };
    case "achievement":
      return {
        text: t("notif.achievement", { icon: n.payload.icon ?? "🏆", name: n.payload.name ?? "" }),
        href: "/achievements",
      };
    case "support_message":
      return { text: t("notif.support", { title: n.payload.title ?? "" }), href: "/inbox" };
    case "application_decided":
      return {
        text: n.payload.status === "approved" ? t("notif.appApproved") : t("notif.appRejected"),
        href: "/dashboard",
      };
    default:
      return { text: t("notif.title") };
  }
}

export function NotificationBell() {
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [items, setItems] = useState<Notif[]>([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const load = useCallback(async () => {
    try {
      const d = await authFetch<{ results: Notif[]; unread: number }>("/api/notifications");
      setItems(d.results);
      setUnread(d.unread);
    } catch {
      /* ignore */
    }
  }, [authFetch]);

  useEffect(() => {
    if (loading || !user) return;
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [loading, user, load]);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && unread > 0) {
      try {
        await authFetch("/api/notifications/read", {
          method: "POST",
          body: JSON.stringify({}),
        });
        setUnread(0);
      } catch {
        /* ignore */
      }
    }
  }

  if (loading || !user) return null;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={toggle}
        className="relative flex h-8 w-8 items-center justify-center rounded-md text-neutral-300 hover:bg-neutral-900"
        aria-label={t("notif.title")}
      >
        <svg
          viewBox="0 0 24 24"
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.7 21a2 2 0 01-3.4 0" />
        </svg>
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-neutral-950">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-72 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 shadow-xl">
          <p className="border-b border-neutral-800 px-3 py-2 text-xs uppercase tracking-wider text-neutral-500">
            {t("notif.title")}
          </p>
          <div className="max-h-80 overflow-y-auto">
            {items.length === 0 ? (
              <p className="px-3 py-6 text-center text-xs text-neutral-500">{t("notif.empty")}</p>
            ) : (
              items.map((n) => {
                const { text, href } = describe(n, t);
                const body = (
                  <div
                    className={`px-3 py-2 text-sm ${
                      n.read_at ? "text-neutral-400" : "text-neutral-100"
                    } hover:bg-neutral-800`}
                  >
                    {text}
                  </div>
                );
                return href ? (
                  <Link key={n.id} href={href} onClick={() => setOpen(false)}>
                    {body}
                  </Link>
                ) : (
                  <div key={n.id}>{body}</div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
