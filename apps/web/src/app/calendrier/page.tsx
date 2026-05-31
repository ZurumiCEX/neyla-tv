"use client";

import { useEffect, useState } from "react";
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

const KIND_COLORS: Record<string, string> = {
  charity: "#FFC81E",
  tournament: "#3b82f6",
  premiere: "#d946ef",
  announcement: "#e5e7eb",
  maintenance: "#f59e0b",
};

export default function CalendrierPage() {
  const t = useT();
  const [events, setEvents] = useState<PlatformEvent[]>([]);
  const [kind, setKind] = useState<string>("");
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    setBusy(true);
    const q = kind ? `?kind=${kind}` : "";
    apiFetch<{ results: PlatformEvent[] }>(`/api/events${q}`)
      .then((d) => setEvents(d.results))
      .catch(() => setEvents([]))
      .finally(() => setBusy(false));
  }, [kind]);

  return (
    <main className="mx-auto max-w-5xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">{t("events.calendarTitle")}</h1>
      </header>

      <div className="mb-4 flex flex-wrap gap-2">
        <Chip active={kind === ""} onClick={() => setKind("")} label="Tout" />
        {(["charity", "tournament", "premiere", "announcement"] as const).map((k) => (
          <Chip
            key={k}
            active={kind === k}
            onClick={() => setKind(k)}
            label={t(`events.kind.${k}`)}
            color={KIND_COLORS[k]}
          />
        ))}
      </div>

      {busy && <p className="text-neutral-500">{t("common.loading")}</p>}

      {!busy && events.length === 0 && (
        <p className="text-sm text-neutral-400">{t("events.empty")}</p>
      )}

      {!busy && events.length > 0 && (
        <ul className="space-y-3">
          {events.map((e) => (
            <li key={e.slug}>
              <Link
                href={e.link_url || `#${e.slug}`}
                className="flex items-center gap-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 transition hover:border-neutral-700"
              >
                <span
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-lg"
                  style={{ background: `${KIND_COLORS[e.kind] ?? "#666"}33`, color: KIND_COLORS[e.kind] }}
                  aria-hidden
                >
                  {{ charity: "❤", tournament: "🏆", premiere: "🎬", announcement: "📣", maintenance: "⚙" }[e.kind]}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold text-neutral-100">{e.title}</p>
                  <p className="text-xs text-neutral-500">
                    {t(`events.kind.${e.kind}`)} ·{" "}
                    {new Date(e.starts_at).toLocaleString("fr-FR", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </p>
                </div>
                {e.is_ongoing && (
                  <span className="shrink-0 rounded bg-red-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-300">
                    {t("events.ongoing")}
                  </span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

function Chip({
  label,
  active,
  onClick,
  color,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  color?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1.5 text-xs transition ${
        active
          ? "border-secondary bg-secondary/15 text-secondary-light"
          : "border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
      }`}
      style={active && color ? { borderColor: color, color } : undefined}
    >
      {label}
    </button>
  );
}
