"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { idempotencyKey } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { fmt, fmtFcfa } from "@/lib/format";
import { useFormat } from "@/lib/use-format";
import { notifyWalletChanged } from "@/lib/wallet-events";
import { CardsLogo, OrangeMoneyLogo, WaveLogo } from "@/components/PaymentLogos";
import { GiftBadgesCard } from "@/components/GiftBadgesCard";
import { LevelBadge, LevelLadder } from "@/components/LevelBadge";
import { useMyLevel } from "@/lib/use-level";
import { AuraLedger } from "@/components/AuraLedger";
import { Eye, EyeOff } from "lucide-react";

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
  payout_hold: boolean;
  recent: Ledger[];
};
type PayoutRow = {
  id: number;
  aura_amount: number;
  fee_aura: number;
  fiat_amount: string;
  currency: string;
  destination_provider: "wave" | "orange_money" | "";
  destination_phone: string;
  status: string;
  created_at: string;
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
  min_aura: number;
  payout_hold: boolean;
  unit_price_xof: string;
};
type Quote = {
  aura: number;
  fee_pct: number;
  fee_aura: number;
  net_aura: number;
  net_fiat: string;
  currency: string;
  min_aura: number;
};
type Paginated<T> = { results: T[] };

const PACKS = [100, 500, 1000, 2500, 5000, 10000];
type Tab = "buy" | "withdraw" | "payments" | "auras";
type Method = "card" | "orange_money" | "wave";

export default function WalletPage() {
  const router = useRouter();
  const t = useT();
  const { date } = useFormat();
  const { user, loading, authFetch } = useAuth();
  const [returnNotice, setReturnNotice] = useState<"pending" | "paid" | "canceled" | null>(null);
  const [wallet, setWallet] = useState<WalletData | null>(null);
  const [tab, setTab] = useState<Tab>("buy");
  const [history, setHistory] = useState<Ledger[] | null>(null);
  const [purchases, setPurchases] = useState<Purchase[] | null>(null);
  const [method, setMethod] = useState<Method>("card");
  const [masked, setMasked] = useState(false);
  const level = useMyLevel();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setWallet(await authFetch<WalletData>("/api/payments/wallet"));
      notifyWalletChanged();
    } catch {
      setError(t("wallet.loadError"));
    }
  }, [authFetch, t]);

  // Retour du checkout Stripe : ?paid=1&purchase=ID → on attend la confirmation
  // (webhook) en interrogeant l'achat, puis on rafraîchit le solde.
  useEffect(() => {
    if (loading || !user) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("canceled")) {
      setReturnNotice("canceled");
      return;
    }
    const id = params.get("purchase");
    if (!params.get("paid") || !id) return;
    setReturnNotice("pending");
    let tries = 0;
    const timer = setInterval(async () => {
      tries += 1;
      try {
        const p = await authFetch<{ status: string }>(`/api/payments/purchases/${id}`);
        if (p.status === "paid") {
          clearInterval(timer);
          setReturnNotice("paid");
          setPurchases(null);
          load();
        } else if (p.status !== "pending" || tries >= 15) {
          clearInterval(timer);
          setReturnNotice(null);
        }
      } catch {
        clearInterval(timer);
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [loading, user, authFetch, load]);

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
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("wallet.buyError"));
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
        <div className="flex items-center gap-3">
          {level && <LevelBadge level={level.level} size={48} />}
          <p className="text-4xl font-bold text-emerald-400">
            {masked ? "••••••" : fmt(wallet.aura_balance)}{" "}
            <span className="text-lg text-neutral-400">Aura</span>
          </p>
        </div>
        <p className="mt-1 text-xs text-neutral-500">
          {t("wallet.unitPrice", { price: wallet.unit_price_xof })}
        </p>
        {wallet.payout_hold && (
          <p className="mt-2 rounded-lg border border-amber-500/40 bg-amber-500/10 p-2 text-xs text-amber-300">
            {t("wallet.payoutHold")}
          </p>
        )}
      </div>

      <div className="mb-6">
        {level && <LevelLadder data={level} masked={masked} />}
        <div className="mt-4">
          <GiftBadgesCard />
        </div>
      </div>

      {returnNotice && (
        <p
          className={`mb-4 rounded-lg border p-3 text-sm ${
            returnNotice === "paid"
              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
              : returnNotice === "canceled"
                ? "border-neutral-700 bg-neutral-900 text-neutral-300"
                : "border-amber-500/40 bg-amber-500/10 text-amber-300"
          }`}
        >
          {t(`wallet.return.${returnNotice}`)}
        </p>
      )}

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
                    <td className="py-2 text-neutral-400">{date(p.created_at)}</td>
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
            <AuraLedger entries={history} />
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
  const { num, date } = useFormat();
  const { authFetch, user } = useAuth();
  const needsTotp = Boolean(user?.two_factor_enabled);
  const [totpCode, setTotpCode] = useState("");
  const [elig, setElig] = useState<Eligibility | null>(null);
  const [payouts, setPayouts] = useState<PayoutRow[] | null>(null);
  const [amount, setAmount] = useState("");
  const [destProvider, setDestProvider] = useState<"wave" | "orange_money">("wave");
  const [phone, setPhone] = useState("");
  const [quote, setQuote] = useState<Quote | null>(null);
  const [step, setStep] = useState<"form" | "otp" | "done">("form");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadElig = useCallback(() => {
    authFetch<Eligibility>("/api/payments/withdrawal/eligibility")
      .then(setElig)
      .catch(() => setElig(null));
    authFetch<Paginated<PayoutRow>>("/api/payments/payouts")
      .then((d) => setPayouts(d.results))
      .catch(() => setPayouts([]));
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
        body: JSON.stringify({
          aura_amount: n,
          destination_provider: destProvider,
          destination_phone: phone.trim(),
        }),
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
        body: JSON.stringify({ code: code.trim(), totp: totpCode.trim() }),
      });
      setStep("done");
      setAmount("");
      setCode("");
      setTotpCode("");
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
          <li>{t("wallet.withdrawInfoMin", { n: num(elig.min_aura) })}</li>
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
              {num(elig.withdrawable)} <span className="text-sm text-neutral-400">Aura</span>
            </p>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-3">
            <p className="text-xs uppercase tracking-wider text-neutral-500">
              {t("wallet.balance")}
            </p>
            <p className="mt-1 text-2xl font-bold">{num(elig.balance)}</p>
          </div>
        </div>

        {error && <p className="mb-3 text-sm text-red-300">{error}</p>}

        {step === "done" && (
          <p className="mb-3 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-3 text-sm text-emerald-300">
            {t("wallet.withdrawDone")}
          </p>
        )}

        {elig.payout_hold && (
          <p className="mb-3 rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-300">
            {t("wallet.payoutHold")}
          </p>
        )}

        {step !== "otp" ? (
          <>
            <label className="mb-1 block text-xs uppercase tracking-wider text-neutral-500">
              {t("wallet.payoutDestination")}
            </label>
            <div className="mb-3 grid grid-cols-[auto_1fr] gap-2">
              <div className="flex gap-1">
                {(["wave", "orange_money"] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setDestProvider(p)}
                    className={`rounded-lg border px-3 py-2 text-xs font-semibold ${
                      destProvider === p
                        ? "border-secondary bg-secondary/10 text-secondary-light"
                        : "border-neutral-700 text-neutral-300 hover:border-neutral-500"
                    }`}
                  >
                    {p === "wave" ? "Wave" : "Orange Money"}
                  </button>
                ))}
              </div>
              <input
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder={t("wallet.payoutPhone")}
                className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
              />
            </div>
            <label className="mb-1 block text-xs uppercase tracking-wider text-neutral-500">
              {t("wallet.withdrawAmount")}
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                min={elig.min_aura}
                max={elig.withdrawable}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder={t("wallet.payoutPlaceholder")}
                className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
              />
              <button
                type="button"
                disabled={
                  busy ||
                  elig.payout_hold ||
                  !quote ||
                  quote.aura > elig.withdrawable ||
                  quote.aura < elig.min_aura ||
                  phone.trim().length < 8
                }
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
              {needsTotp && (
                <input
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  placeholder={t("wallet.totpPlaceholder")}
                  aria-label={t("wallet.totpPlaceholder")}
                  className="w-40 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-center text-sm text-neutral-100 outline-none focus:border-secondary-light"
                />
              )}
              <button
                type="button"
                disabled={
                  busy || code.trim().length < 6 || (needsTotp && totpCode.trim().length < 6)
                }
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

      <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-neutral-400">
          {t("wallet.payoutHistory")}
        </h3>
        {payouts === null ? (
          <p className="text-sm text-neutral-500">{t("common.loading")}</p>
        ) : payouts.length === 0 ? (
          <p className="text-sm text-neutral-500">{t("wallet.payoutNone")}</p>
        ) : (
          <table className="w-full text-left text-sm">
            <tbody>
              {payouts.map((p) => (
                <tr key={p.id} className="border-t border-neutral-800/60">
                  <td className="py-2 text-neutral-500">{date(p.created_at)}</td>
                  <td className="py-2 text-neutral-300">
                    {num(p.aura_amount)} Aura → {fmtFcfa(p.fiat_amount)}
                  </td>
                  <td className="py-2 text-neutral-400">
                    {p.destination_provider === "orange_money" ? "Orange Money" : "Wave"}{" "}
                    {p.destination_phone}
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
      : status === "failed" || status === "refunded" || status === "disputed"
        ? "border-red-500/40 text-red-300"
        : "border-amber-500/40 text-amber-300";
  return (
    <span className={`rounded-full border px-2 py-0.5 text-xs ${cls}`}>
      {t(`wallet.status.${status}`)}
    </span>
  );
}

function EyeIcon({ off }: { off: boolean }) {
  return off ? <EyeOff size={18} aria-hidden /> : <Eye size={18} aria-hidden />;
}
