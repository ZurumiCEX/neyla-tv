"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";

type Fee = {
  id: number;
  product: string;
  mode: string;
  value: string;
  is_active: boolean;
};

const PRODUCTS = [
  { value: "tip", label: "Tip" },
  { value: "subscription", label: "Abonnement" },
  { value: "purchase", label: "Achat" },
];

export default function AdminFeesPage() {
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
      setError("Chargement impossible.");
    }
  }, [authFetch]);

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
      setError("Création impossible.");
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
      <p className="text-sm text-neutral-400">
        La règle active la plus récente d&apos;un produit définit la commission plateforme.
        Sans règle, le partage par défaut (70 % créateur) s&apos;applique.
      </p>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
        <label className="flex flex-col gap-1 text-xs text-neutral-500">
          Produit
          <select
            value={product}
            onChange={(e) => setProduct(e.target.value)}
            className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
          >
            {PRODUCTS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-neutral-500">
          Mode
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
          >
            <option value="percentage">Pourcentage</option>
            <option value="fixed">Montant fixe</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-neutral-500">
          Commission {mode === "percentage" ? "(%)" : "(Aura)"}
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
          Ajouter
        </button>
      </div>

      {error && <p className="text-sm text-red-300">{error}</p>}

      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase tracking-wider text-neutral-500">
          <tr>
            <th className="pb-2">Produit</th>
            <th className="pb-2">Mode</th>
            <th className="pb-2">Commission</th>
            <th className="pb-2">Active</th>
            <th className="pb-2" />
          </tr>
        </thead>
        <tbody>
          {fees.map((f) => (
            <tr key={f.id} className="border-t border-neutral-800/60">
              <td className="py-2 capitalize text-neutral-200">{f.product}</td>
              <td className="py-2 text-neutral-400">{f.mode}</td>
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
                  {f.is_active ? "Active" : "Inactive"}
                </button>
              </td>
              <td className="py-2">
                <button
                  type="button"
                  onClick={() => remove(f.id)}
                  className="text-xs text-red-300 hover:underline"
                >
                  Supprimer
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {fees.length === 0 && <p className="text-sm text-neutral-500">Aucune règle définie.</p>}
    </div>
  );
}
