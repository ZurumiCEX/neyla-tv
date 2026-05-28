"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Fee = {
  id: number;
  product: string;
  mode: string;
  value: string;
  is_active: boolean;
};

const PRODUCTS = ["tip", "subscription", "purchase"];

export default function AdminFeesPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const [fees, setFees] = useState<Fee[]>([]);
  const [product, setProduct] = useState("tip");
  const [mode, setMode] = useState("percentage");
  const [value, setValue] = useState("30");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setFees(await authFetch<Fee[]>("/api/admin/fees"));
    } catch {
      setError(t("common.loadError"));
    }
  }, [authFetch, t]);

  useEffect(() => {
    load();
  }, [load]);

  async function create() {
    setError(null);
    try {
      await authFetch("/api/admin/fees", {
        method: "POST",
        body: JSON.stringify({ product, mode, value }),
      });
      load();
    } catch {
      setError(t("admin.fees.createError"));
    }
  }

  async function toggle(fee: Fee) {
    await authFetch(`/api/admin/fees/${fee.id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !fee.is_active }),
    });
    load();
  }

  async function remove(id: number) {
    await authFetch(`/api/admin/fees/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-neutral-400">{t("admin.fees.intro")}</p>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
        <label className="flex flex-col gap-1 text-xs text-neutral-500">
          {t("admin.fees.product")}
          <select
            value={product}
            onChange={(e) => setProduct(e.target.value)}
            className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
          >
            {PRODUCTS.map((p) => (
              <option key={p} value={p}>
                {t(`admin.product.${p}`)}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-neutral-500">
          {t("admin.fees.mode")}
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
          >
            <option value="percentage">{t("admin.feemode.percentage")}</option>
            <option value="fixed">{t("admin.feemode.fixed")}</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-neutral-500">
          {t("admin.fees.commission")} {mode === "percentage" ? "(%)" : "(Aura)"}
          <input
            type="number"
            min={0}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-32 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
          />
        </label>
        <button
          type="button"
          onClick={create}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
        >
          {t("admin.fees.add")}
        </button>
      </div>

      {error && <p className="text-sm text-red-300">{error}</p>}

      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase tracking-wider text-neutral-500">
          <tr>
            <th className="pb-2">{t("admin.fees.product")}</th>
            <th className="pb-2">{t("admin.fees.mode")}</th>
            <th className="pb-2">{t("admin.fees.commission")}</th>
            <th className="pb-2">{t("admin.fees.colActive")}</th>
            <th className="pb-2" />
          </tr>
        </thead>
        <tbody>
          {fees.map((f) => (
            <tr key={f.id} className="border-t border-neutral-800/60">
              <td className="py-2 text-neutral-200">{t(`admin.product.${f.product}`)}</td>
              <td className="py-2 text-neutral-400">{t(`admin.feemode.${f.mode}`)}</td>
              <td className="py-2 text-neutral-300">
                {f.value}
                {f.mode === "percentage" ? " %" : " Aura"}
              </td>
              <td className="py-2">
                <button
                  type="button"
                  onClick={() => toggle(f)}
                  className={`rounded px-2 py-1 text-xs font-semibold ${
                    f.is_active
                      ? "bg-emerald-500/20 text-emerald-300"
                      : "bg-neutral-700 text-neutral-300"
                  }`}
                >
                  {f.is_active ? t("admin.fees.active") : t("admin.fees.inactive")}
                </button>
              </td>
              <td className="py-2">
                <button
                  type="button"
                  onClick={() => remove(f.id)}
                  className="text-xs text-red-300 hover:underline"
                >
                  {t("admin.fees.delete")}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {fees.length === 0 && <p className="text-sm text-neutral-500">{t("admin.fees.empty")}</p>}
    </div>
  );
}
