"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type RiskEvent = {
  id: number;
  username: string;
  kind: string;
  severity: number;
  detail: Record<string, unknown>;
  resolved: boolean;
  created_at: string;
};
type ContentFlag = {
  id: number;
  username: string;
  channel_slug: string;
  source: string;
  category: string;
  confidence: number;
  text: string;
  url: string;
  status: string;
  created_at: string;
};
type Overview = { open_risk_events: number; pending_flags: number; auto_blocked: number };

const SEVERITY: Record<number, { label: string; cls: string }> = {
  1: { label: "Faible", cls: "border-neutral-600 text-neutral-300" },
  2: { label: "Moyen", cls: "border-amber-500/40 text-amber-300" },
  3: { label: "Élevé", cls: "border-red-500/40 text-red-300" },
};

export default function AdminSafetyPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const [tab, setTab] = useState<"flags" | "risk">("flags");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [flags, setFlags] = useState<ContentFlag[] | null>(null);
  const [risks, setRisks] = useState<RiskEvent[] | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    authFetch<Overview>("/api/admin/safety/overview").then(setOverview).catch(() => undefined);
    authFetch<{ results: ContentFlag[] }>("/api/admin/safety/flags")
      .then((d) => setFlags(d.results))
      .catch(() => setFlags([]));
    authFetch<{ results: RiskEvent[] }>("/api/admin/safety/risk-events?unresolved=1")
      .then((d) => setRisks(d.results))
      .catch(() => setRisks([]));
  }, [authFetch]);

  useEffect(() => {
    load();
  }, [load]);

  async function resolveFlag(id: number, action: "approve" | "reject") {
    setBusy(true);
    try {
      await authFetch(`/api/admin/safety/flags/${id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      load();
    } finally {
      setBusy(false);
    }
  }

  async function resolveRisk(id: number) {
    setBusy(true);
    try {
      await authFetch(`/api/admin/safety/risk-events/${id}/resolve`, { method: "POST" });
      load();
    } finally {
      setBusy(false);
    }
  }

  const cards: [string, number, string][] = overview
    ? [
        [t("safety.pendingFlags"), overview.pending_flags, "#f59e0b"],
        [t("safety.autoBlocked"), overview.auto_blocked, "#ef4444"],
        [t("safety.openRisks"), overview.open_risk_events, "#3b82f6"],
      ]
    : [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {cards.map(([label, value, color]) => (
          <div
            key={label}
            className="relative overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4"
          >
            <span className="absolute left-0 top-0 h-full w-1" style={{ backgroundColor: color }} />
            <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
            <p className="mt-1 text-2xl font-bold">{value}</p>
          </div>
        ))}
      </div>

      <div className="flex gap-1 border-b border-neutral-800">
        {(["flags", "risk"] as const).map((tb) => (
          <button
            key={tb}
            type="button"
            onClick={() => setTab(tb)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition ${
              tab === tb
                ? "border-emerald-500 text-emerald-300"
                : "border-transparent text-neutral-400 hover:text-neutral-200"
            }`}
          >
            {tb === "flags" ? t("safety.tab.flags") : t("safety.tab.risk")}
          </button>
        ))}
      </div>

      {tab === "flags" && (
        <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60">
          {flags === null ? (
            <p className="p-6 text-sm text-neutral-500">{t("common.loading")}</p>
          ) : flags.length === 0 ? (
            <p className="p-6 text-sm text-neutral-500">{t("safety.noFlags")}</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-neutral-900/80 text-xs uppercase tracking-wider text-neutral-500">
                <tr>
                  <th className="px-4 py-3">{t("safety.col.category")}</th>
                  <th className="px-4 py-3">{t("safety.col.source")}</th>
                  <th className="px-4 py-3">{t("safety.col.subject")}</th>
                  <th className="px-4 py-3">{t("safety.col.content")}</th>
                  <th className="px-4 py-3">{t("safety.col.status")}</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {flags.map((f) => (
                  <tr key={f.id} className="border-t border-neutral-800/60 hover:bg-neutral-800/30">
                    <td className="px-4 py-2.5">
                      <CategoryPill category={f.category} label={t(`safety.cat.${f.category}`)} />
                    </td>
                    <td className="px-4 py-2.5 text-neutral-400">{t(`safety.src.${f.source}`)}</td>
                    <td className="px-4 py-2.5 text-neutral-200">
                      {f.channel_slug ? `@${f.channel_slug}` : f.username ? `@${f.username}` : "—"}
                    </td>
                    <td className="px-4 py-2.5 max-w-[16rem] truncate text-neutral-400">
                      {f.text || f.url || "—"}
                    </td>
                    <td className="px-4 py-2.5 text-neutral-400">{t(`safety.st.${f.status}`)}</td>
                    <td className="px-4 py-2.5">
                      {(f.status === "pending" || f.status === "auto_blocked") && (
                        <span className="flex gap-2">
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => resolveFlag(f.id, "approve")}
                            className="rounded border border-neutral-700 px-2 py-1 text-xs hover:border-emerald-500 hover:text-emerald-300"
                          >
                            {t("safety.approve")}
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => resolveFlag(f.id, "reject")}
                            className="rounded bg-red-500/80 px-2 py-1 text-xs font-semibold text-neutral-950 hover:bg-red-400"
                          >
                            {t("safety.reject")}
                          </button>
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === "risk" && (
        <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60">
          {risks === null ? (
            <p className="p-6 text-sm text-neutral-500">{t("common.loading")}</p>
          ) : risks.length === 0 ? (
            <p className="p-6 text-sm text-neutral-500">{t("safety.noRisks")}</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-neutral-900/80 text-xs uppercase tracking-wider text-neutral-500">
                <tr>
                  <th className="px-4 py-3">{t("safety.col.user")}</th>
                  <th className="px-4 py-3">{t("safety.col.signal")}</th>
                  <th className="px-4 py-3">{t("safety.col.severity")}</th>
                  <th className="px-4 py-3">{t("safety.col.detail")}</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {risks.map((r) => (
                  <tr key={r.id} className="border-t border-neutral-800/60 hover:bg-neutral-800/30">
                    <td className="px-4 py-2.5 text-neutral-200">@{r.username}</td>
                    <td className="px-4 py-2.5 text-neutral-300">{t(`safety.kind.${r.kind}`)}</td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`rounded-full border px-2 py-0.5 text-xs ${
                          SEVERITY[r.severity]?.cls ?? ""
                        }`}
                      >
                        {SEVERITY[r.severity]?.label ?? r.severity}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs text-neutral-500">
                      {JSON.stringify(r.detail)}
                    </td>
                    <td className="px-4 py-2.5">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => resolveRisk(r.id)}
                        className="rounded border border-neutral-700 px-2 py-1 text-xs hover:border-emerald-500 hover:text-emerald-300"
                      >
                        {t("safety.markReviewed")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

function CategoryPill({ category, label }: { category: string; label: string }) {
  const cls =
    category === "sexual"
      ? "border-fuchsia-500/40 text-fuchsia-300"
      : category === "gore"
        ? "border-red-500/40 text-red-300"
        : category === "safe"
          ? "border-emerald-500/40 text-emerald-300"
          : "border-neutral-600 text-neutral-300";
  return <span className={`rounded-full border px-2 py-0.5 text-xs ${cls}`}>{label}</span>;
}
