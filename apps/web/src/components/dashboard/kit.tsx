"use client";

// Dashboard streamer : contexte partagé (chaîne du propriétaire) + briques d'UI
// (panneau type widget, interrupteur, champ, statistique, chronomètre de live).

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Maximize2, Minimize2, type LucideIcon } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

export type Category = { slug: string; name: string };

export type MyChannel = {
  slug: string;
  title: string;
  thumbnail_url: string;
  ingest_url: string;
  stream_key: string;
  playback_url: string;
  stream_checked_at: string | null;
  is_live: boolean;
  is_provisioned: boolean;
  last_live_started_at: string | null;
  category: Category | null;
  tags: string[];
  overlay_token: string;
  collaborations_open: boolean;
  goal_title: string;
  goal_kind: "subs" | "tips";
  goal_target: number;
  follower_count?: number;
  viewers?: number;
  active_subs?: number;
};

type DashboardState = {
  channel: MyChannel | null;
  error: string | null;
  setChannel: (c: MyChannel) => void;
  reload: () => Promise<void>;
};

const DashboardContext = createContext<DashboardState | null>(null);

export function useDashboard(): DashboardState {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error("useDashboard hors du DashboardProvider");
  return ctx;
}

/** Charge la chaîne du streamer et la rafraîchit (compteurs live) toutes les 15 s. */
export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [channel, setChannel] = useState<MyChannel | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setChannel(await authFetch<MyChannel>("/api/channels/me"));
      setError(null);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.loadError"));
    }
  }, [authFetch, t]);

  useEffect(() => {
    if (!user) return;
    reload();
    const id = setInterval(() => {
      if (document.visibilityState === "visible") reload();
    }, 15_000);
    return () => clearInterval(id);
  }, [user, reload]);

  return (
    <DashboardContext.Provider value={{ channel, error, setChannel, reload }}>
      {children}
    </DashboardContext.Provider>
  );
}

/** Panneau façon widget (titre + icône + actions), agrandissable en plein écran. */
export function Panel({
  title,
  icon: Icon,
  actions,
  children,
  className = "",
  bodyClassName = "p-4",
  expandable = true,
}: {
  title: string;
  icon?: LucideIcon;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
  expandable?: boolean;
}) {
  const t = useT();
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!expanded) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setExpanded(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [expanded]);

  return (
    <section
      className={`flex min-h-0 flex-col overflow-hidden rounded-lg border border-neutral-800 bg-neutral-900 ${
        expanded ? "fixed inset-3 z-[60] shadow-2xl sm:inset-8" : className
      }`}
    >
      <header className="flex h-12 shrink-0 items-center gap-2.5 border-b border-neutral-800 px-4">
        {Icon && <Icon size={18} className="shrink-0 text-neutral-300" aria-hidden />}
        <h2 className="min-w-0 flex-1 truncate text-[15px] font-bold">{title}</h2>
        {actions}
        {expandable && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-label={expanded ? t("dash2.collapse") : t("dash2.expand")}
            title={expanded ? t("dash2.collapse") : t("dash2.expand")}
            className="flex h-7 w-7 items-center justify-center rounded-md text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
          >
            {expanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          </button>
        )}
      </header>
      <div className={`min-h-0 flex-1 overflow-auto ${bodyClassName}`}>{children}</div>
      {expanded && (
        <button
          type="button"
          aria-hidden
          tabIndex={-1}
          onClick={() => setExpanded(false)}
          className="fixed inset-0 -z-10 bg-black/70"
        />
      )}
    </section>
  );
}

/** Interrupteur accessible (role=switch). */
export function Switch({
  checked,
  onChange,
  label,
  disabled,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative h-6 w-11 shrink-0 rounded-full transition disabled:opacity-50 ${
        checked ? "bg-emerald-500" : "bg-neutral-700"
      }`}
    >
      <span
        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
          checked ? "left-[22px]" : "left-0.5"
        }`}
      />
    </button>
  );
}

/** Ligne de réglage : libellé + description + contrôle à droite. */
export function SettingRow({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-2.5">
      <div className="min-w-0">
        <p className="text-sm font-semibold text-neutral-100">{label}</p>
        {hint && <p className="text-xs text-neutral-500">{hint}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

/** Sélecteur « ‹ valeur › » façon Kick (cycle dans une liste d'options). */
export function Stepper<T extends string | number>({
  value,
  options,
  onChange,
  render,
  label,
}: {
  value: T;
  options: readonly T[];
  onChange: (v: T) => void;
  render: (v: T) => string;
  label: string;
}) {
  const idx = Math.max(0, options.indexOf(value));
  const step = (d: number) => onChange(options[(idx + d + options.length) % options.length]);
  const btn =
    "flex h-8 w-8 items-center justify-center rounded-md border border-neutral-700 text-neutral-300 hover:border-neutral-500 hover:text-neutral-100";
  return (
    <div className="flex items-center gap-2" role="group" aria-label={label}>
      <button type="button" onClick={() => step(-1)} className={btn} aria-label="−">
        ‹
      </button>
      <span className="min-w-24 text-center text-sm font-bold">{render(value)}</span>
      <button type="button" onClick={() => step(1)} className={btn} aria-label="+">
        ›
      </button>
    </div>
  );
}

export function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-950/40 p-4">
      <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
      <p className="mt-1 text-2xl font-bold tabular-nums">{value}</p>
    </div>
  );
}

/** Durée du live en cours, rafraîchie chaque seconde. */
export function LiveTimer({ startedAt }: { startedAt: string }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (now === null) return <span>—</span>;
  const s = Math.max(0, Math.floor((now - new Date(startedAt).getTime()) / 1000));
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    <span className="tabular-nums">
      {pad(Math.floor(s / 3600))}:{pad(Math.floor((s % 3600) / 60))}:{pad(s % 60)}
    </span>
  );
}

export const inputCls =
  "w-full rounded-md border border-neutral-700 bg-neutral-950 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-400";
