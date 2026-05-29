"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Tx = {
  type: string;
  id: number;
  user: string;
  aura: number;
  status: string;
  created_at: string;
  detail: string;
};

type Page = { count: number; next: string | null; results: Tx[] };

const TYPES = [
  { value: "", key: "admin.txtype.all" },
  { value: "purchase", key: "admin.txtype.purchase" },
  { value: "tip", key: "admin.txtype.tip" },
  { value: "subscription", key: "admin.txtype.subscription" },
  { value: "payout", key: "admin.txtype.payout" },
];

export default function AdminTransactionsPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const [rows, setRows] = useState<Tx[]>([]);
  const [count, setCount] = useState(0);
  const [type, setType] = useState("");
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const params = new URLSearchParams();
    if (type) params.set("type", type);
    if (q.trim()) params.set("q", q.trim());
    try {
      const data = await authFetch<Page>(`/api/admin/transactions?${params.toString()}`);
      setRows(data.results);
      setCount(data.count);
    } catch {
      setError(t("common.loadError"));
    }
  }, [authFetch, type, q, t]);

  useEffect(() => {
    load();
  }, [load]);

  async function resolvePayout(id: number, action: "paid" | "fail") {
    try {
      await authFetch(`/api/admin/payouts/${id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      load();
    } catch {
      setError(t("admin.actionError"));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-4">
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-secondary-light"
        >
          {TYPES.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {t(opt.key)}
            </option>
          ))}
        </select>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t("admin.tx.searchUser")}
          className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-secondary-light"
        />
        <span className="ml-auto rounded-full bg-neutral-800 px-3 py-1 text-sm text-neutral-300">
          {t("admin.tx.results", { count })}
        </span>
      </div>

      {error && <p className="text-sm text-red-300">{error}</p>}

      <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-900/60">
        <table className="w-full text-left text-sm">
          <thead className="bg-neutral-900/80 text-xs uppercase tracking-wider text-neutral-500">
            <tr>
              <th className="px-4 py-3">{t("admin.tx.colType")}</th>
              <th className="px-4 py-3">{t("admin.tx.colUser")}</th>
              <th className="px-4 py-3 text-right">{t("admin.tx.colAura")}</th>
              <th className="px-4 py-3">{t("admin.tx.colDetail")}</th>
              <th className="px-4 py-3">{t("admin.tx.colStatus")}</th>
              <th className="px-4 py-3">{t("admin.tx.colDate")}</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={`${r.type}-${r.id}`}
                className="border-t border-neutral-800/60 hover:bg-neutral-800/30"
              >
                <td className="px-4 py-2.5">
                  <TypeBadge type={r.type} label={t(`admin.txtype.${r.type}`)} />
                </td>
                <td className="px-4 py-2.5 text-neutral-200">@{r.user}</td>
                <td className="px-4 py-2.5 text-right font-mono tabular-nums text-neutral-200">
                  {r.aura.toLocaleString("fr-FR")}
                </td>
                <td className="px-4 py-2.5 text-neutral-400">{r.detail}</td>
                <td className="px-4 py-2.5">
                  <StatusPill status={r.status} />
                </td>
                <td className="px-4 py-2.5 text-neutral-500">
                  {new Date(r.created_at).toLocaleDateString("fr-FR", {
                    day: "2-digit",
                    month: "short",
                  })}
                </td>
                <td className="px-4 py-2.5">
                  {r.type === "payout" && r.status === "requested" && (
                    <span className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => resolvePayout(r.id, "paid")}
                        className="rounded bg-emerald-500 px-2 py-1 text-xs font-semibold text-neutral-950 hover:bg-emerald-400"
                      >
                        {t("admin.tx.pay")}
                      </button>
                      <button
                        type="button"
                        onClick={() => resolvePayout(r.id, "fail")}
                        className="rounded bg-red-500/80 px-2 py-1 text-xs font-semibold text-neutral-950 hover:bg-red-400"
                      >
                        {t("admin.tx.reject")}
                      </button>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && !error && (
          <p className="p-6 text-sm text-neutral-500">{t("admin.tx.empty")}</p>
        )}
      </div>
    </div>
  );
}

const TYPE_COLORS: Record<string, string> = {
  purchase: "#FFC81E",
  tip: "#3b82f6",
  subscription: "#d946ef",
  payout: "#f59e0b",
};

function TypeBadge({ type, label }: { type: string; label: string }) {
  const color = TYPE_COLORS[type] ?? "#9ca3af";
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ color, backgroundColor: `${color}1a` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

function StatusPill({ status }: { status: string }) {
  const ok = ["paid", "active", "completed"].includes(status);
  const pending = ["requested", "pending"].includes(status);
  const cls = ok
    ? "border-emerald-500/40 text-emerald-300"
    : pending
      ? "border-amber-500/40 text-amber-300"
      : ["failed", "canceled", "expired"].includes(status)
        ? "border-red-500/40 text-red-300"
        : "border-neutral-700 text-neutral-400";
  return <span className={`rounded-full border px-2 py-0.5 text-xs ${cls}`}>{status}</span>;
}
