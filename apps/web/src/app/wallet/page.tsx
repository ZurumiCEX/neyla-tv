"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Ledger = {
  amount: number;
  kind: string;
  reference: string;
  balance_after: number;
  created_at: string;
};
type FiatEq = { xof: string; eur: string; usd: string };
type WalletData = {
  aura_balance: number;
  balance: FiatEq;
  unit_price_xof: string;
  recent: Ledger[];
};

const PACKS = [100, 500, 1000, 5000];

export default function WalletPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [busy, setBusy] = useState(false);
  const [payoutAmount, setPayoutAmount] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setWallet(await authFetch<WalletData>("/api/payments/wallet"));
    } catch {
      setError(t("wallet.loadError"));
    }
  }, [authFetch, t]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [loading, user, load, router]);

  async function buy(credits: number) {
    setBusy(true);
    setError(null);
    try {
      const res = await authFetch<{ status: string; checkout_url: string | null }>(
        "/api/payments/purchase",
        { method: "POST", body: JSON.stringify({ credits }) },
      );
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
        return;
      }
      await load();
    } catch {
      setError(t("wallet.buyError"));
    } finally {
      setBusy(false);
    }
  }

  async function payout() {
    const amount = parseInt(payoutAmount, 10);
    if (!amount || amount <= 0) return;
    setBusy(true);
    setError(null);
    try {
      await authFetch("/api/payments/payout", {
        method: "POST",
        body: JSON.stringify({ aura_amount: amount }),
      });
      setPayoutAmount("");
      await load();
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("wallet.payoutError"));
    } finally {
      setBusy(false);
    }
  }

  if (loading || !wallet) return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-2 text-2xl font-bold">{t("wallet.title")}</h1>
      <p className="text-4xl font-bold text-emerald-400">
        {wallet.aura_balance} <span className="text-lg text-neutral-400">Aura</span>
      </p>
      <p className="mb-6 mt-1 text-sm text-neutral-400">
        ≈ {wallet.balance.xof} FCFA{" "}
        <span className="text-neutral-600">
          ({wallet.balance.eur} € / {wallet.balance.usd} $)
        </span>
      </p>

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
        <h2 className="mb-3 font-semibold">{t("wallet.buyTitle")}</h2>
        <div className="flex flex-wrap gap-2">
          {PACKS.map((p) => (
            <button
              key={p}
              type="button"
              disabled={busy}
              onClick={() => buy(p)}
              className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
            >
              {p} Aura
              <span className="ml-1 font-normal opacity-80">
                · {p * Number(wallet.unit_price_xof)} FCFA
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
        <h2 className="mb-3 font-semibold">{t("wallet.payoutTitle")}</h2>
        <div className="flex gap-2">
          <input
            type="number"
            min={1}
            value={payoutAmount}
            onChange={(e) => setPayoutAmount(e.target.value)}
            placeholder={t("wallet.payoutPlaceholder")}
            className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-500"
          />
          <button
            type="button"
            disabled={busy}
            onClick={payout}
            className="rounded-lg border border-neutral-700 px-4 py-2 text-sm hover:border-neutral-500 disabled:opacity-50"
          >
            {t("wallet.payoutRequest")}
          </button>
        </div>
      </section>

      <h2 className="mb-3 font-semibold">{t("wallet.history")}</h2>
      {wallet.recent.length === 0 ? (
        <p className="text-sm text-neutral-500">{t("wallet.noOps")}</p>
      ) : (
        <table className="w-full text-left text-sm">
          <tbody>
            {wallet.recent.map((l, i) => (
              <tr key={i} className="border-t border-neutral-800/60">
                <td className="py-2 text-neutral-400">{t(`wallet.kind.${l.kind}`)}</td>
                <td
                  className={`py-2 text-right font-semibold ${
                    l.amount >= 0 ? "text-emerald-300" : "text-red-300"
                  }`}
                >
                  {l.amount >= 0 ? "+" : ""}
                  {l.amount}
                </td>
                <td className="py-2 text-right text-neutral-500">{l.balance_after}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
