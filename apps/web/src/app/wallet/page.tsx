"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AURA_TIERS, AuraBadge, auraTier, nextAuraTier } from "@/components/AuraBadge";
import { idempotencyKey } from "@/lib/api";
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
type Purchase = {
  id: number;
  credits: number;
  fiat_amount: string;
  currency: string;
  provider: string;
  status: string;
  created_at: string;
};
type Paginated<T> = { results: T[] };

const PACKS = [100, 500, 1000, 5000];
type Tab = "wallet" | "payments" | "auras";

export default function WalletPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [tab, setTab] = useState<Tab>("wallet");
  const [history, setHistory] = useState<Ledger[] | null>(null);
  const [purchases, setPurchases] = useState<Purchase[] | null>(null);
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

  useEffect(() => {
    if (!user) return;
    if (tab === "auras" && history === null) {
      authFetch<Paginated<Ledger>>("/api/payments/history")
        .then((d) => setHistory(d.results))
        .catch(() => setHistory([]));
    }
    if (tab === "payments" && purchases === null) {
      authFetch<Paginated<Purchase>>("/api/payments/purchases")
        .then((d) => setPurchases(d.results))
        .catch(() => setPurchases([]));
    }
  }, [tab, user, history, purchases, authFetch]);

  async function buy(credits: number) {
    setBusy(true);
    setError(null);
    try {
      const res = await authFetch<{ status: string; checkout_url: string | null }>(
        "/api/payments/purchase",
        {
          method: "POST",
          body: JSON.stringify({ credits }),
          headers: { "Idempotency-Key": idempotencyKey() },
        },
      );
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
        return;
      }
      setPurchases(null);
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
        headers: { "Idempotency-Key": idempotencyKey() },
      });
      setPayoutAmount("");
      setHistory(null);
      await load();
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("wallet.payoutError"));
    } finally {
      setBusy(false);
    }
  }

  if (loading || !wallet)
    return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  const tier = auraTier(wallet.aura_balance);
  const next = nextAuraTier(wallet.aura_balance);
  const progress = next
    ? Math.min(100, Math.round((wallet.aura_balance / next.min) * 100))
    : 100;

  const tabs: { id: Tab; label: string }[] = [
    { id: "wallet", label: t("wallet.tab.wallet") },
    { id: "payments", label: t("wallet.tab.payments") },
    { id: "auras", label: t("wallet.tab.auras") },
  ];

  return (
    <main className="mx-auto max-w-3xl p-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="mb-2 text-2xl font-bold">{t("wallet.title")}</h1>
          <p className="text-4xl font-bold text-emerald-400">
            {wallet.aura_balance} <span className="text-lg text-neutral-400">Aura</span>
          </p>
          <p className="mt-1 text-sm text-neutral-400">
            ≈ {wallet.balance.xof} FCFA{" "}
            <span className="text-neutral-600">
              ({wallet.balance.eur} € / {wallet.balance.usd} $)
            </span>
          </p>
        </div>
        {tier && (
          <div className="flex items-center gap-2 rounded-xl border border-neutral-800 bg-neutral-900/60 px-3 py-2">
            <AuraBadge tier={tier} size={36} />
            <div>
              <p className="text-sm font-semibold" style={{ color: tier.color }}>
                {t(`aura.tier.${tier.key}`)}
              </p>
              {next && (
                <p className="text-xs text-neutral-500">
                  {t("wallet.nextTier", {
                    n: (next.min - wallet.aura_balance).toLocaleString("fr-FR"),
                    tier: t(`aura.tier.${next.key}`),
                  })}
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      <div className="mb-6 flex gap-1 border-b border-neutral-800">
        {tabs.map((tb) => (
          <button
            key={tb.id}
            type="button"
            onClick={() => setTab(tb.id)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition ${
              tab === tb.id
                ? "border-emerald-500 text-emerald-300"
                : "border-transparent text-neutral-400 hover:text-neutral-200"
            }`}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {tab === "wallet" && (
        <>
          {next && (
            <div className="mb-6">
              <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-800">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${progress}%`, backgroundColor: next.color }}
                />
              </div>
            </div>
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

          <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
            <h2 className="mb-4 font-semibold">{t("wallet.tierLegend")}</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              {AURA_TIERS.map((tr) => {
                const reached = wallet.aura_balance >= tr.min;
                return (
                  <div key={tr.key} className="flex items-center gap-2">
                    <AuraBadge tier={tr} size={32} locked={!reached} />
                    <div className="min-w-0">
                      <p
                        className="truncate text-sm font-medium"
                        style={{ color: reached ? tr.color : "#71717a" }}
                      >
                        {t(`aura.tier.${tr.key}`)}
                      </p>
                      <p className="text-xs text-neutral-500">
                        {tr.min.toLocaleString("fr-FR")}+ Aura
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </>
      )}

      {tab === "payments" && (
        <section>
          {purchases === null ? (
            <p className="text-sm text-neutral-500">{t("common.loading")}</p>
          ) : purchases.length === 0 ? (
            <p className="text-sm text-neutral-500">{t("wallet.purchasesNone")}</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-neutral-500">
                <tr>
                  <th className="py-2">{t("wallet.col.date")}</th>
                  <th className="py-2">{t("wallet.col.credits")}</th>
                  <th className="py-2 text-right">{t("wallet.col.amount")}</th>
                  <th className="py-2 text-right">{t("wallet.col.status")}</th>
                </tr>
              </thead>
              <tbody>
                {purchases.map((p) => (
                  <tr key={p.id} className="border-t border-neutral-800/60">
                    <td className="py-2 text-neutral-400">
                      {new Date(p.created_at).toLocaleDateString("fr-FR")}
                    </td>
                    <td className="py-2 text-emerald-300">+{p.credits} Aura</td>
                    <td className="py-2 text-right text-neutral-300">
                      {p.fiat_amount} {p.currency}
                    </td>
                    <td className="py-2 text-right">
                      <StatusPill status={p.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {tab === "auras" && (
        <section>
          {history === null ? (
            <p className="text-sm text-neutral-500">{t("common.loading")}</p>
          ) : history.length === 0 ? (
            <p className="text-sm text-neutral-500">{t("wallet.noOps")}</p>
          ) : (
            <table className="w-full text-left text-sm">
              <tbody>
                {history.map((l, i) => (
                  <tr key={i} className="border-t border-neutral-800/60">
                    <td className="py-2 text-neutral-500">
                      {new Date(l.created_at).toLocaleDateString("fr-FR")}
                    </td>
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
        </section>
      )}
    </main>
  );
}

function StatusPill({ status }: { status: string }) {
  const t = useT();
  const cls =
    status === "paid"
      ? "border-emerald-500/40 text-emerald-300"
      : status === "failed"
        ? "border-red-500/40 text-red-300"
        : "border-amber-500/40 text-amber-300";
  return (
    <span className={`rounded-full border px-2 py-0.5 text-xs ${cls}`}>
      {t(`wallet.status.${status}`)}
    </span>
  );
}
