"use client";

// Graphes légers en SVG pur (aucune dépendance) — thème sombre Neyla.

import { useId } from "react";

function buildPaths(values: number[], w: number, h: number, pad = 2) {
  const n = values.length;
  if (n === 0) return { line: "", area: "" };
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const x = (i: number) => (n === 1 ? w / 2 : (i / (n - 1)) * w);
  const y = (v: number) => h - pad - ((v - min) / range) * (h - pad * 2);
  const line = values.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(2)} ${y(v).toFixed(2)}`).join(" ");
  const area = `${line} L${x(n - 1).toFixed(2)} ${h} L${x(0).toFixed(2)} ${h} Z`;
  return { line, area };
}

export function Sparkline({
  values,
  color = "#10b981",
  className = "",
}: {
  values: number[];
  color?: string;
  className?: string;
}) {
  const id = useId().replace(/:/g, "");
  const { line, area } = buildPaths(values, 100, 32);
  return (
    <svg
      viewBox="0 0 100 32"
      preserveAspectRatio="none"
      className={className}
      aria-hidden
    >
      <defs>
        <linearGradient id={`spark-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {area && <path d={area} fill={`url(#spark-${id})`} />}
      {line && (
        <path
          d={line}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          vectorEffect="non-scaling-stroke"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}

export function AreaChart({
  values,
  labels,
  color = "#10b981",
  formatY = (v: number) => String(v),
  height = 280,
}: {
  values: number[];
  labels: string[];
  color?: string;
  formatY?: (v: number) => string;
  height?: number;
}) {
  const id = useId().replace(/:/g, "");
  const W = 600;
  const H = 220;
  const { line, area } = buildPaths(values, W, H, 6);
  const max = Math.max(...values, 1);
  const gridLines = [0, 0.25, 0.5, 0.75, 1];
  // Étiquettes X espacées (max ~7).
  const step = Math.max(1, Math.ceil(labels.length / 7));

  return (
    <div className="w-full" style={{ height }}>
      <div className="flex h-full">
        <div className="flex w-12 flex-col justify-between py-1 text-right text-[10px] text-neutral-600">
          {gridLines
            .slice()
            .reverse()
            .map((g) => (
              <span key={g}>{formatY(Math.round(max * g))}</span>
            ))}
        </div>
        <div className="relative flex-1">
          <svg
            viewBox={`0 0 ${W} ${H}`}
            preserveAspectRatio="none"
            className="h-[calc(100%-18px)] w-full"
          >
            <defs>
              <linearGradient id={`area-${id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity="0.35" />
                <stop offset="100%" stopColor={color} stopOpacity="0.02" />
              </linearGradient>
            </defs>
            {gridLines.map((g) => (
              <line
                key={g}
                x1="0"
                x2={W}
                y1={6 + g * (H - 12)}
                y2={6 + g * (H - 12)}
                stroke="#262626"
                strokeWidth="1"
                vectorEffect="non-scaling-stroke"
              />
            ))}
            {area && <path d={area} fill={`url(#area-${id})`} />}
            {line && (
              <path
                d={line}
                fill="none"
                stroke={color}
                strokeWidth="2"
                vectorEffect="non-scaling-stroke"
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            )}
          </svg>
          <div className="flex justify-between text-[10px] text-neutral-600">
            {labels.map((l, i) => (
              <span key={i} className={i % step === 0 ? "" : "invisible"}>
                {l}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export type DonutSegment = { label: string; value: number; color: string };

export function Donut({
  segments,
  centerValue,
  centerLabel,
  size = 160,
}: {
  segments: DonutSegment[];
  centerValue: string;
  centerLabel: string;
  size?: number;
}) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  const r = 60;
  const c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <svg viewBox="0 0 160 160" width={size} height={size} aria-hidden>
      <g transform="rotate(-90 80 80)">
        <circle cx="80" cy="80" r={r} fill="none" stroke="#1f1f1f" strokeWidth="16" />
        {segments.map((s) => {
          const frac = s.value / total;
          const dash = frac * c;
          const el = (
            <circle
              key={s.label}
              cx="80"
              cy="80"
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth="16"
              strokeDasharray={`${dash} ${c - dash}`}
              strokeDashoffset={-offset}
              strokeLinecap="butt"
            />
          );
          offset += dash;
          return el;
        })}
      </g>
      <text x="80" y="76" textAnchor="middle" className="fill-neutral-100 text-[20px] font-bold">
        {centerValue}
      </text>
      <text x="80" y="96" textAnchor="middle" className="fill-neutral-500 text-[10px]">
        {centerLabel}
      </text>
    </svg>
  );
}

export function ProgressBar({
  label,
  value,
  hint,
  color = "#10b981",
}: {
  label: string;
  value: number;
  hint?: string;
  color?: string;
}) {
  const pct = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-neutral-300">{label}</span>
        <span className="font-semibold text-neutral-100">{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-800">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      {hint && <p className="mt-1 text-xs text-neutral-500">{hint}</p>}
    </div>
  );
}
