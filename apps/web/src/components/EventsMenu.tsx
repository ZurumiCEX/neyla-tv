"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";

type PlatformEvent = {
  slug: string;
  title: string;
  kind: "charity" | "tournament" | "premiere" | "announcement" | "maintenance";
  cover_url: string;
  link_url: string;
  starts_at: string;
  ends_at: string;
  is_ongoing: boolean;
};

export function EventsMenu() {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [events, setEvents] = useState<PlatformEvent[]>([]);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  useEffect(() => {
    apiFetch<{ results: PlatformEvent[] }>("/api/events/upcoming?limit=5")
      .then((d) => setEvents(d.results))
      .catch(() => setEvents([]));
  }, []);

  const ongoingCount = events.filter((e) => e.is_ongoing).length;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={t("nav.events")}
        title={t("nav.events")}
        className="relative flex h-9 w-9 items-center justify-center rounded-full text-neutral-300 hover:bg-neutral-800 hover:text-neutral-100"
      >
        <svg
          viewBox="0 0 24 24"
          width="18"
          height="18"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <rect x="3" y="4" width="18" height="17" rx="2" />
          <path d="M16 2v4M8 2v4M3 10h18" />
        </svg>
        {ongoingCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-neutral-950 bg-red-500" />
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 shadow-xl">
          <div className="border-b border-neutral-800 px-4 py-3">
            <p className="text-sm font-semibold text-neutral-100">{t("events.upcomingTitle")}</p>
          </div>
          <div className="max-h-80 overflow-y-auto py-1">
            {events.length === 0 ? (
              <p className="px-4 py-3 text-sm text-neutral-500">{t("events.empty")}</p>
            ) : (
              events.map((e) => (
                <Link
                  key={e.slug}
                  href={e.link_url || `/calendrier#${e.slug}`}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-3 px-4 py-2.5 hover:bg-neutral-800"
                >
                  <span
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-xs font-bold"
                    style={{ background: kindColor(e.kind), color: "#0a0a0a" }}
                    aria-hidden
                  >
                    {kindIcon(e.kind)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm text-neutral-100">{e.title}</span>
                    <span className="block truncate text-xs text-neutral-500">
                      {t(`events.kind.${e.kind}`)} · {formatRelative(e.starts_at)}
                    </span>
                  </span>
                  {e.is_ongoing && (
                    <span className="shrink-0 rounded bg-red-500/20 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-300">
                      {t("events.ongoing")}
                    </span>
                  )}
                </Link>
              ))
            )}
          </div>
          <Link
            href="/calendrier"
            onClick={() => setOpen(false)}
            className="block border-t border-neutral-800 px-4 py-2.5 text-center text-sm font-semibold text-secondary-light hover:bg-secondary/10"
          >
            {t("events.seeAll")}
          </Link>
        </div>
      )}
    </div>
  );
}

function kindColor(kind: string): string {
  return (
    {
      charity: "#FFC81E",
      tournament: "#3b82f6",
      premiere: "#d946ef",
      maintenance: "#f59e0b",
      announcement: "#e5e7eb",
    }[kind] ?? "#e5e7eb"
  );
}

function kindIcon(kind: string): string {
  return (
    {
      charity: "❤",
      tournament: "🏆",
      premiere: "🎬",
      maintenance: "⚙",
      announcement: "📣",
    }[kind] ?? "•"
  );
}

function formatRelative(iso: string): string {
  const d = new Date(iso);
  const now = Date.now();
  const diff = d.getTime() - now;
  const days = Math.round(diff / 86400000);
  if (Math.abs(days) < 1) return d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  if (days >= 0 && days < 7) return `dans ${days} j`;
  return d.toLocaleDateString("fr-FR");
}
