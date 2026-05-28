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
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm"
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
          className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm"
        />
        <span className="text-sm text-neutral-500">{t("admin.tx.results", { count })}</span>
      </div>

      {error && <p className="mb-3 text-sm text-red-300">{error}</p>}

      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase tracking-wider text-neutral-500">
          <tr>
            <th className="pb-2">{t("admin.tx.colType")}</th>
            <th className="pb-2">{t("admin.tx.colUser")}</th>
            <th className="pb-2">{t("admin.tx.colAura")}</th>
            <th className="pb-2">{t("admin.tx.colDetail")}</th>
            <th className="pb-2">{t("admin.tx.colStatus")}</th>
            <th className="pb-2">{t("admin.tx.colDate")}</th>
            <th className="pb-2" />
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.type}-${r.id}`} className="border-t border-neutral-800/60">
              <td className="py-2 capitalize text-neutral-300">{r.type}</td>
              <td className="py-2 text-neutral-200">@{r.user}</td>
              <td className="py-2 text-neutral-300">{r.aura}</td>
              <td className="py-2 text-neutral-400">{r.detail}</td>
              <td className="py-2 text-neutral-400">{r.status}</td>
              <td className="py-2 text-neutral-500">
                {new Date(r.created_at).toLocaleDateString("fr-FR", {
                  day: "2-digit",
                  month: "short",
                })}
              </td>
              <td className="py-2">
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
        <p className="mt-4 text-sm text-neutral-500">{t("admin.tx.empty")}</p>
      )}
    </div>
  );
}
