"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { idempotencyKey } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { fmt, fmtFcfa } from "@/lib/format";
import { CardsLogo, OrangeMoneyLogo, WaveLogo } from "@/components/PaymentLogos";

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
type Eligibility = {
  is_streamer: boolean;
  balance: number;
  withdrawable: number;
  fee_pct: number;
  unit_price_xof: string;
};
type Quote = {
  aura: number;
  fee_pct: number;
  fee_aura: number;
  net_aura: number;
  net_fiat: string;
};
type Paginated<T> = { results: T[] };

const PACKS = [100, 500, 1000, 2500, 5000, 10000];
type Tab = "buy" | "withdraw" | "payments" | "auras";
type Method = "card" | "orange_money" | "wave";

export default function WalletPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [tab, setTab] = useState<Tab>("buy");
  const [history, setHistory] = useState<Ledger[] | null>(null);
  const [purchases, setPurchases] = useState<Purchase[] | null>(null);
  const [method, setMethod] = useState<Method>("card");
  const [masked, setMasked] = useState(false);
  const [busy, setBusy] = useState(false);
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
          body: JSON.stringify({ credits, method }),
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

  if (loading || !wallet)
    return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;

  const tabs: { id: Tab; label: string }[] = [
    { id: "buy", label: t("wallet.tab.buy") },
    { id: "withdraw", label: t("wallet.tab.withdraw") },
    { id: "payments", label: t("wallet.tab.payments") },
    { id: "auras", label: t("wallet.tab.auras") },
  ];

  return (
    <main className="mx-auto max-w-3xl p-8">
      <div className="mb-6">
        <div className="mb-2 flex items-center gap-2">
          <h1 className="text-2xl font-bold">{t("wallet.title")}</h1>
          <button
            type="button"
            onClick={() => setMasked((m) => !m)}
            aria-label={masked ? t("wallet.show") : t("wallet.hide")}
            title={masked ? t("wallet.show") : t("wallet.hide")}
            className="rounded-full p-1.5 text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
          >
            <EyeIcon off={masked} />
          </button>
        </div>
        <p className="text-4xl font-bold text-emerald-400">
          {masked ? "••••••" : fmt(wallet.aura_balance)}{" "}
          <span className="text-lg text-neutral-400">Aura</span>
        </p>
        <p className="mt-1 text-sm text-neutral-400">
          ≈ {masked ? "••••" : fmtFcfa(wallet.balance.xof)}{" "}
          {!masked && (
            <span className="text-neutral-600">
              ({wallet.balance.eur} € / {wallet.balance.usd} $)
            </span>
          )}
        </p>
      </div>

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      <div className="mb-6 flex flex-wrap gap-1 border-b border-neutral-800">
        {tabs.map((tb) => (
          <button
            key={tb.id}
            type="button"
            onClick={() => setTab(tb.id)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition ${
              tab === tb.id
                ? "border-secondary text-secondary-light"
                : "border-transparent text-neutral-400 hover:text-neutral-200"
            }`}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {tab === "buy" && (
        <>
          <section className="mb-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
            <h2 className="mb-3 font-semibold">{t("wallet.payMethod")}</h2>
            <div className="grid grid-cols-3 gap-2">
              <MethodButton active={method === "wave"} onClick={() => setMethod("wave")}>
                <WaveLogo />
              </MethodButton>
              <MethodButton active={method === "card"} onClick={() => setMethod("card")}>
                <CardsLogo />
              </MethodButton>
              <MethodButton
                active={method === "orange_money"}
                onClick={() => setMethod("orange_money")}
              >
                <OrangeMoneyLogo />
              </MethodButton>
            </div>
          </section>

          <section className="mb-8 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
            <h2 className="mb-3 font-semibold">{t("wallet.buyTitle")}</h2>
            {/* Packs sur 2 lignes max (grille 3×2). */}
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {PACKS.map((p) => (
                <button
                  key={p}
                  type="button"
                  disabled={busy}
                  onClick={() => buy(p)}
                  className="rounded-lg bg-emerald-500 px-3 py-2 text-center text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
                >
                  <span className="block">{fmt(p)} Aura</span>
                  <span className="block text-xs font-normal opacity-80">
                    {fmtFcfa(p * Number(wallet.unit_price_xof))}
                  </span>
                </button>
              ))}
            </div>
            <p className="mt-3 text-xs text-neutral-500">
              {t("wallet.payVia", { method: methodLabel(method, t) })}
            </p>
          </section>
        </>
      )}

      {tab === "withdraw" && <WithdrawTab onDone={load} />}

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
                    <td className="py-2 text-emerald-300">+{fmt(p.credits)} Aura</td>
                    <td className="py-2 text-right text-neutral-300">
                      {fmt(p.fiat_amount)} {p.currency}
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
                      {fmt(l.amount)}
                    </td>
                    <td className="py-2 text-right text-neutral-500">{fmt(l.balance_after)}</td>
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

function methodLabel(m: Method, t: (k: string) => string): string {
  if (m === "card") return t("wallet.method.card");
  if (m === "orange_money") return "Orange Money";
  return "Wave";
}

function MethodButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex h-16 items-center justify-center rounded-xl border bg-white/95 p-2 transition ${
        active
          ? "border-emerald-500 ring-2 ring-emerald-500/40"
          : "border-neutral-700 hover:border-secondary"
      }`}
    >
      {children}
    </button>
  );
}

function WithdrawTab({ onDone }: { onDone: () => void }) {
  const t = useT();
  const { authFetch } = useAuth();
  const [elig, setElig] = useState<Eligibility | null>(null);
  const [amount, setAmount] = useState("");
  const [quote, setQuote] = useState<Quote | null>(null);
  const [step, setStep] = useState<"form" | "otp" | "done">("form");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadElig = useCallback(() => {
    authFetch<Eligibility>("/api/payments/withdrawal/eligibility")
      .then(setElig)
      .catch(() => setElig(null));
  }, [authFetch]);

  useEffect(() => {
    loadElig();
  }, [loadElig]);

  useEffect(() => {
    const n = parseInt(amount, 10);
    if (!n || n <= 0) {
      setQuote(null);
      return;
    }
    const id = setTimeout(() => {
      authFetch<Quote>("/api/payments/withdrawal/quote", {
        method: "POST",
        body: JSON.stringify({ aura_amount: n }),
      })
        .then(setQuote)
        .catch(() => setQuote(null));
    }, 300);
    return () => clearTimeout(id);
  }, [amount, authFetch]);

  async function start() {
    const n = parseInt(amount, 10);
    if (!n || n <= 0) return;
    setBusy(true);
    setError(null);
    try {
      await authFetch("/api/payments/withdrawal/start", {
        method: "POST",
        body: JSON.stringify({ aura_amount: n }),
      });
      setStep("otp");
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("wallet.payoutError"));
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      await authFetch("/api/payments/withdrawal/confirm", {
        method: "POST",
        body: JSON.stringify({ code: code.trim() }),
      });
      setStep("done");
      setAmount("");
      setCode("");
      loadElig();
      onDone();
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("wallet.otpError"));
    } finally {
      setBusy(false);
    }
  }

  if (!elig) return <p className="text-sm text-neutral-500">{t("common.loading")}</p>;

  if (!elig.is_streamer) {
    return (
      <section className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5">
        <p className="font-semibold text-amber-300">{t("wallet.streamerOnly")}</p>
        <p className="mt-1 text-sm text-neutral-300">{t("wallet.streamerOnlyDesc")}</p>
      </section>
    );
  }

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-blue-500/30 bg-blue-500/5 p-4 text-sm text-neutral-300">
        <p className="font-semibold text-blue-300">{t("wallet.withdrawInfoTitle")}</p>
        <ul className="mt-2 list-inside list-disc space-y-1 text-neutral-400">
          <li>{t("wallet.withdrawInfo1")}</li>
          <li>{t("wallet.withdrawInfo2", { pct: elig.fee_pct })}</li>
          <li>{t("wallet.withdrawInfo3")}</li>
        </ul>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
        <div className="mb-4 grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-3">
            <p className="text-xs uppercase tracking-wider text-neutral-500">
              {t("wallet.withdrawable")}
            </p>
            <p className="mt-1 text-2xl font-bold text-emerald-400">
              {elig.withdrawable.toLocaleString("fr-FR")}{" "}
              <span className="text-sm text-neutral-400">Aura</span>
            </p>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-3">
            <p className="text-xs uppercase tracking-wider text-neutral-500">
              {t("wallet.balance")}
            </p>
            <p className="mt-1 text-2xl font-bold">{elig.balance.toLocaleString("fr-FR")}</p>
          </div>
        </div>

        {error && <p className="mb-3 text-sm text-red-300">{error}</p>}

        {step === "done" && (
          <p className="mb-3 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-3 text-sm text-emerald-300">
            {t("wallet.withdrawDone")}
          </p>
        )}

        {step !== "otp" ? (
          <>
            <label className="mb-1 block text-xs uppercase tracking-wider text-neutral-500">
              {t("wallet.withdrawAmount")}
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                min={1}
                max={elig.withdrawable}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder={t("wallet.payoutPlaceholder")}
                className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
              />
              <button
                type="button"
                disabled={busy || !quote || quote.aura > elig.withdrawable}
                onClick={start}
                className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
              >
                {t("wallet.requestWithdraw")}
              </button>
            </div>
            {quote && quote.aura > 0 && (
              <div className="mt-3 rounded-lg border border-neutral-800 bg-neutral-900/40 p-3 text-sm">
                <Row label={t("wallet.quoteGross")} value={`${fmt(quote.aura)} Aura`} />
                <Row
                  label={t("wallet.quoteFee", { pct: quote.fee_pct })}
                  value={`- ${fmt(quote.fee_aura)} Aura`}
                  red
                />
                <div className="my-2 border-t border-neutral-800" />
                <Row
                  label={t("wallet.quoteNet")}
                  value={`${fmt(quote.net_aura)} Aura ≈ ${fmtFcfa(quote.net_fiat)}`}
                  strong
                />
              </div>
            )}
          </>
        ) : (
          <div>
            <p className="mb-2 text-sm text-neutral-300">{t("wallet.otpPrompt")}</p>
            <div className="flex gap-2">
              <input
                inputMode="numeric"
                autoComplete="one-time-code"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="123456"
                className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-center text-lg tracking-widest text-neutral-100 outline-none focus:border-secondary-light"
              />
              <button
                type="button"
                disabled={busy || code.trim().length < 6}
                onClick={confirm}
                className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
              >
                {t("wallet.confirmWithdraw")}
              </button>
            </div>
            <button
              type="button"
              onClick={() => {
                setStep("form");
                setCode("");
                setError(null);
              }}
              className="mt-2 text-xs text-neutral-500 hover:text-neutral-300"
            >
              {t("common.cancel")}
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function Row({
  label,
  value,
  red,
  strong,
}: {
  label: string;
  value: string;
  red?: boolean;
  strong?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-neutral-400">{label}</span>
      <span
        className={`${red ? "text-red-300" : strong ? "font-semibold text-emerald-300" : "text-neutral-200"}`}
      >
        {value}
      </span>
    </div>
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

function EyeIcon({ off }: { off: boolean }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
      {off && <path d="M3 3l18 18" />}
    </svg>
  );
}
