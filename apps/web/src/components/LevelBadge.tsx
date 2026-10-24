"use client";

import { useId } from "react";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

// Niveaux : Aura dépensée à vie (tips, abonnements, abos offerts, dons).
// Emblèmes facettés (face claire / face sombre), prestige croissant :
// bronze → argent → or → améthyste → émeraude → irisé (G.O.A.T).
export type LevelKey = "rookie" | "beginner" | "casual" | "great" | "lord" | "mvp" | "goat";

export type Level = {
  key: LevelKey;
  min: number;
  color: string;
  light: string;
  dark: string;
  glow: string;
};

export const LEVELS: Level[] = [
  {
    key: "beginner",
    min: 10_000,
    color: "#d08b4f",
    light: "#e6a46a",
    dark: "#8c5a2b",
    glow: "rgba(208,139,79,0.45)",
  },
  {
    key: "casual",
    min: 50_000,
    color: "#cbd5e1",
    light: "#e2e8f0",
    dark: "#8b97a8",
    glow: "rgba(203,213,225,0.45)",
  },
  {
    key: "great",
    min: 100_000,
    color: "#FFC81E",
    light: "#ffd95e",
    dark: "#c99400",
    glow: "rgba(255,200,30,0.5)",
  },
  {
    key: "lord",
    min: 200_000,
    color: "#a855f7",
    light: "#c084fc",
    dark: "#6d28d9",
    glow: "rgba(168,85,247,0.5)",
  },
  {
    key: "mvp",
    min: 500_000,
    color: "#10b981",
    light: "#34d399",
    dark: "#047857",
    glow: "rgba(16,185,129,0.5)",
  },
  {
    key: "goat",
    min: 1_000_000,
    color: "#f472b6",
    light: "#fbcfe8",
    dark: "#db2777",
    glow: "rgba(244,114,182,0.6)",
  },
];

export function levelByKey(key?: string | null): Level | null {
  return LEVELS.find((l) => l.key === key) ?? null;
}

export type LevelProgress = {
  level: LevelKey;
  next_level: LevelKey | null;
  next_at: number | null;
  progress: number;
  spent?: number;
};

function Emblem({ level, gradientId }: { level: Level; gradientId: string }) {
  const { light: L, dark: D } = level;
  switch (level.key) {
    case "beginner":
      // Écu + un chevron.
      return (
        <g className="aura-float">
          <path d="M24 4 L41 10 V24 C41 34 33 41 24 44 Z" fill={D} />
          <path d="M24 4 L7 10 V24 C7 34 15 41 24 44 Z" fill={L} />
          <path d="M14 22 L24 28 L34 22 V27 L24 33 L14 27 Z" fill="#fff" opacity="0.85" />
        </g>
      );
    case "casual":
      // Écu + deux chevrons + étoile.
      return (
        <g className="aura-float">
          <path d="M24 3 L42 9 V24 C42 35 34 42 24 45 Z" fill={D} />
          <path d="M24 3 L6 9 V24 C6 35 14 42 24 45 Z" fill={L} />
          <polygon
            points="24,9 26,14 31,14 27,17 28.5,22 24,19 19.5,22 21,17 17,14 22,14"
            fill="#fff"
          />
          <path d="M14 25 L24 30 L34 25 V29 L24 34 L14 29 Z" fill="#fff" opacity="0.85" />
          <path d="M14 32 L24 37 L34 32 V35 L24 40 L14 35 Z" fill="#fff" opacity="0.6" />
        </g>
      );
    case "great":
      // Médaillon à lauriers + étoile.
      return (
        <g className="aura-breathe">
          <circle cx="24" cy="24" r="15" fill={D} />
          <path d="M24 9 A15 15 0 0 0 24 39 Z" fill={L} />
          <polygon
            points="24,14 27,21 34,21 28.5,25.5 30.5,33 24,28.5 17.5,33 19.5,25.5 14,21 21,21"
            fill="#fff"
          />
          {[0, 1, 2, 3].map((i) => (
            <g key={i}>
              <ellipse
                cx={8 + i * 0.8}
                cy={34 - i * 7}
                rx="2.6"
                ry="4.6"
                transform={`rotate(${-35 + i * 12} ${8 + i * 0.8} ${34 - i * 7})`}
                fill={L}
              />
              <ellipse
                cx={40 - i * 0.8}
                cy={34 - i * 7}
                rx="2.6"
                ry="4.6"
                transform={`rotate(${35 - i * 12} ${40 - i * 0.8} ${34 - i * 7})`}
                fill={D}
              />
            </g>
          ))}
        </g>
      );
    case "lord":
      // Couronne facettée.
      return (
        <g className="aura-breathe">
          <path d="M6 16 L15 24 L24 8 L24 36 L8 36 Z" fill={L} />
          <path d="M42 16 L33 24 L24 8 L24 36 L40 36 Z" fill={D} />
          <rect x="8" y="37" width="32" height="5" rx="1.5" fill={D} />
          <rect x="8" y="37" width="16" height="5" rx="1.5" fill={L} />
          <circle cx="24" cy="8" r="2.6" fill="#fff" />
          <circle cx="6" cy="16" r="2.2" fill="#fff" />
          <circle cx="42" cy="16" r="2.2" fill="#fff" />
          <polygon points="24,22 28,27 24,32 20,27" fill="#fff" opacity="0.9" />
        </g>
      );
    case "mvp":
      // Trophée facetté.
      return (
        <g className="aura-shimmer">
          <path d="M12 6 H24 V30 C17 30 12 24 12 17 Z" fill={L} />
          <path d="M36 6 H24 V30 C31 30 36 24 36 17 Z" fill={D} />
          <path
            d="M12 9 H5 C5 17 9 21 13 21"
            fill="none"
            stroke={L}
            strokeWidth="3"
            strokeLinecap="round"
          />
          <path
            d="M36 9 H43 C43 17 39 21 35 21"
            fill="none"
            stroke={D}
            strokeWidth="3"
            strokeLinecap="round"
          />
          <rect x="21" y="30" width="6" height="7" fill={D} />
          <path d="M14 38 H34 L36 44 H12 Z" fill={L} />
          <polygon
            points="24,11 26.5,16 32,16.5 28,20 29,25.5 24,23 19,25.5 20,20 16,16.5 21.5,16"
            fill="#fff"
          />
        </g>
      );
    case "goat":
      // Diamant couronné irisé + rayons.
      return (
        <>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#f472b6" />
              <stop offset="35%" stopColor="#a78bfa" />
              <stop offset="65%" stopColor="#22d3ee" />
              <stop offset="100%" stopColor="#FFC81E" />
            </linearGradient>
          </defs>
          <g className="aura-rays">
            {[0, 45, 90, 135, 180, 225, 270, 315].map((r) => (
              <polygon
                key={r}
                transform={`rotate(${r} 24 24)`}
                points="22.5,6 25.5,6 24,0.5"
                fill={`url(#${gradientId})`}
              />
            ))}
          </g>
          <g className="aura-breathe level-iridescent">
            <path
              d="M12 15 L17 19 L24 10 L31 19 L36 15 L34 22 H14 Z"
              fill={`url(#${gradientId})`}
            />
            <polygon points="14,23 34,23 24,42" fill={`url(#${gradientId})`} />
            <polygon points="14,23 24,23 24,42" fill="#fff" opacity="0.35" />
            <polygon points="19,23 24,30 29,23" fill="#fff" opacity="0.55" />
          </g>
        </>
      );
    default:
      // Rookie : hexagone neutre.
      return (
        <g>
          <polygon points="24,6 39,15 39,33 24,42 9,33 9,15" fill="#3f3f46" />
          <polygon points="24,6 9,15 9,33 24,42" fill="#52525b" />
          <circle cx="24" cy="24" r="5" fill="#a1a1aa" />
        </g>
      );
  }
}

const ROOKIE: Level = {
  key: "rookie",
  min: 0,
  color: "#a1a1aa",
  light: "#52525b",
  dark: "#3f3f46",
  glow: "transparent",
};

export function LevelBadge({
  level,
  size = 32,
  animated = true,
  locked = false,
}: {
  level: string | null | undefined;
  size?: number;
  animated?: boolean;
  locked?: boolean;
}) {
  const gradientId = `lvl-${useId().replace(/:/g, "")}`;
  const meta = levelByKey(level) ?? ROOKIE;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden
      className={`aura-badge shrink-0 ${animated && !locked ? "aura-animated" : ""}`}
      style={{
        filter: locked ? "grayscale(1)" : `drop-shadow(0 0 ${size > 30 ? 6 : 3}px ${meta.glow})`,
        opacity: locked ? 0.35 : 1,
      }}
    >
      <Emblem level={meta} gradientId={gradientId} />
    </svg>
  );
}

/** Pastille niveau : emblème + nom (header, profil, chat). */
export function LevelPill({
  level,
  size = 18,
}: {
  level: string | null | undefined;
  size?: number;
}) {
  const t = useT();
  const meta = levelByKey(level);
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-bold"
      style={{ borderColor: meta?.color ?? "#52525b", color: meta?.color ?? "#a1a1aa" }}
    >
      <LevelBadge level={level} size={size} />
      {t(`level.${level ?? "rookie"}`)}
    </span>
  );
}

/** Échelle des 6 niveaux avec le niveau actuel et la progression vers le suivant. */
export function LevelLadder({ data, masked = false }: { data: LevelProgress; masked?: boolean }) {
  const t = useT();
  const { num } = useFormat();
  const current = levelByKey(data.level);
  const next = levelByKey(data.next_level);
  const remaining =
    data.next_at !== null && typeof data.spent === "number" ? data.next_at - data.spent : null;

  return (
    <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4 sm:p-5">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-neutral-300">
            {t("level.ladder.title")}
          </h2>
          <p className="text-xs text-neutral-500">{t("level.ladder.desc")}</p>
        </div>
        <p className="text-xs text-neutral-400">
          {next && remaining !== null
            ? t("level.ladder.toNext", {
                n: masked ? "•••" : num(remaining),
                level: t(`level.${next.key}`),
              })
            : next
              ? t(`level.${next.key}`)
              : t("level.ladder.max")}
        </p>
      </div>

      <ol className="grid grid-cols-3 gap-2 sm:grid-cols-6 sm:gap-3">
        {LEVELS.map((lvl) => {
          const reached = current !== null && lvl.min <= current.min;
          const isCurrent = current?.key === lvl.key;
          return (
            <li
              key={lvl.key}
              aria-current={isCurrent ? "step" : undefined}
              className={`flex flex-col items-center rounded-xl border px-1 py-3 text-center ${
                isCurrent ? "bg-neutral-950" : "border-transparent"
              }`}
              style={
                isCurrent
                  ? { borderColor: lvl.color, boxShadow: `0 0 18px -6px ${lvl.glow}` }
                  : undefined
              }
            >
              <span className="flex h-12 items-center sm:h-14">
                <LevelBadge level={lvl.key} size={44} locked={!reached} animated={isCurrent} />
              </span>
              <span
                className="mt-2 text-xs font-bold sm:text-sm"
                style={{ color: reached ? lvl.color : undefined }}
              >
                {t(`level.${lvl.key}`)}
              </span>
              <span className="mt-0.5 text-[11px] tabular-nums text-neutral-500">
                {num(lvl.min)} Aura
              </span>
            </li>
          );
        })}
      </ol>

      {next && (
        <div
          className="mt-4 h-2 overflow-hidden rounded-full bg-neutral-800"
          role="progressbar"
          aria-valuenow={data.progress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className="h-full rounded-full transition-[width] duration-700"
            style={{
              width: `${data.progress}%`,
              background: `linear-gradient(90deg, ${current?.color ?? "#525252"}, ${next.color})`,
            }}
          />
        </div>
      )}
    </section>
  );
}
