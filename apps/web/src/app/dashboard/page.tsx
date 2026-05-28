"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { CopyButton } from "@/components/CopyButton";
import { LiveBadge } from "@/components/LiveBadge";

type TFn = (key: string, params?: Record<string, string | number>) => string;

type Category = { slug: string; name: string };

type MyChannel = {
  slug: string;
  title: string;
  thumbnail_url: string;
  rtmps_url: string;
  rtmps_key: string;
  hls_playback_url: string;
  is_live: boolean;
  is_provisioned: boolean;
  last_live_started_at: string | null;
  category: Category | null;
  follower_count?: number;
  viewers?: number;
};

type StreamSession = {
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  peak_viewers: number;
  category: string | null;
};

type MyStats = {
  sessions_total: number;
  broadcast_hours: number;
  peak_viewers: number;
  follower_count: number;
};

type SubTier = {
  name?: string;
  price_aura?: number;
  perks?: string[];
  is_active?: boolean;
};

function formatDuration(seconds: number | null, t: TFn): string {
  if (seconds === null) return t("dash.durationOngoing");
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h > 0 ? `${h}h${String(m).padStart(2, "0")}` : t("dash.durationMin", { m });
}

export default function DashboardPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [channel, setChannel] = useState<MyChannel | null>(null);
  const [sessions, setSessions] = useState<StreamSession[]>([]);
  const [stats, setStats] = useState<MyStats | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [rotating, setRotating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [revealKey, setRevealKey] = useState(false);

  // Form state mirror.
  const [title, setTitle] = useState("");
  const [categorySlug, setCategorySlug] = useState("");

  // Subscription tier config.
  const [tierPrice, setTierPrice] = useState("100");
  const [tierPerks, setTierPerks] = useState("");
  const [tierActive, setTierActive] = useState(true);
  const [tierSaving, setTierSaving] = useState(false);
  const [tierSaved, setTierSaved] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await authFetch<MyChannel>("/api/channels/me");
      setChannel(data);
      setTitle(data.title);
      setCategorySlug(data.category?.slug ?? "");
      if (data.is_provisioned) {
        authFetch<{ results: StreamSession[] }>("/api/channels/me/sessions")
          .then((d) => setSessions(d.results))
          .catch(() => undefined);
        authFetch<MyStats>("/api/analytics/me")
          .then(setStats)
          .catch(() => undefined);
        authFetch<SubTier>("/api/streamer/tier")
          .then((tier) => {
            if (typeof tier.price_aura === "number") {
              setTierPrice(String(tier.price_aura));
              setTierPerks((tier.perks ?? []).join("\n"));
              setTierActive(tier.is_active ?? true);
            }
          })
          .catch(() => undefined);
      }
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.loadError"));
    }
  }, [authFetch, t]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
    apiFetch<{ results: Category[] }>("/api/discover/categories?limit=100")
      .then((d) => setCategories(d.results))
      .catch(() => undefined);
  }, [loading, user, load, router]);

  async function save() {
    setSaving(true);
    try {
      const data = await authFetch<MyChannel>("/api/channels/me", {
        method: "PATCH",
        body: JSON.stringify({
          title,
          category_slug: categorySlug || null,
        }),
      });
      setChannel(data);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.saveError"));
    } finally {
      setSaving(false);
    }
  }

  async function rotate() {
    setRotating(true);
    try {
      const data = await authFetch<MyChannel>("/api/channels/me/key/rotate", {
        method: "POST",
      });
      setChannel(data);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.rotateError"));
    } finally {
      setRotating(false);
    }
  }

  async function saveTier() {
    setTierSaving(true);
    setTierSaved(false);
    try {
      const perks = tierPerks
        .split("\n")
        .map((p) => p.trim())
        .filter(Boolean);
      await authFetch("/api/streamer/tier", {
        method: "PUT",
        body: JSON.stringify({
          price_aura: Number(tierPrice) || 1,
          perks,
          is_active: tierActive,
        }),
      });
      setTierSaved(true);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.tierSaveError"));
    } finally {
      setTierSaving(false);
    }
  }

  if (loading || (!user && !error)) {
    return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;
  }

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="mb-6 text-2xl font-bold">{t("dash.title")}</h1>

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {channel && (
        <section className="space-y-6 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
          <header className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold">@{channel.slug}</h2>
              {channel.is_provisioned && (
                <LiveBadge slug={channel.slug} initial={{ is_live: channel.is_live }} />
              )}
            </div>
            <Link
              href={`/c/${channel.slug}`}
              className="text-sm text-emerald-300 underline"
            >
              {t("dash.publicPage")}
            </Link>
          </header>

          <div className="flex gap-6 text-sm text-neutral-400">
            <span>
              <span className="font-semibold text-neutral-100">
                {channel.follower_count ?? 0}
              </span>{" "}
              {t("dash.followers")}
            </span>
            <span>
              <span className="font-semibold text-neutral-100">
                {channel.viewers ?? 0}
              </span>{" "}
              {t("dash.currentViewers")}
            </span>
          </div>

          <div className="space-y-3 border-b border-neutral-800 pb-6">
            <Field label={t("dash.streamTitle")}>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={140}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-500"
              />
            </Field>
            <Field label={t("dash.category")}>
              <select
                value={categorySlug}
                onChange={(e) => setCategorySlug(e.target.value)}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-emerald-500"
              >
                <option value="">{t("dash.categoryNone")}</option>
                {categories.map((c) => (
                  <option key={c.slug} value={c.slug}>
                    {c.name}
                  </option>
                ))}
              </select>
            </Field>
            <button
              type="button"
              onClick={save}
              disabled={saving}
              className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
            >
              {saving ? t("common.saving") : t("common.save")}
            </button>
          </div>

          {channel.is_provisioned ? (
            <>
              <Field label={t("dash.status")}>
                <span className="text-emerald-300">{t("dash.approved")}</span>
              </Field>

              <Field label={t("dash.rtmpsServer")}>
                <div className="flex items-center gap-2">
                  <code className="break-all text-emerald-300">
                    {channel.rtmps_url || "—"}
                  </code>
                  {channel.rtmps_url && <CopyButton value={channel.rtmps_url} />}
                </div>
              </Field>

              <Field label={t("dash.streamKey")}>
                <div className="flex items-center gap-2">
                  <code className="break-all text-emerald-300">
                    {channel.rtmps_key
                      ? revealKey
                        ? channel.rtmps_key
                        : "•".repeat(Math.min(channel.rtmps_key.length, 40))
                      : "—"}
                  </code>
                  {channel.rtmps_key && (
                    <>
                      <button
                        type="button"
                        onClick={() => setRevealKey((v) => !v)}
                        className="rounded-md border border-neutral-700 px-2 py-1 text-xs text-neutral-300 hover:border-neutral-500"
                      >
                        {revealKey ? t("dash.hide") : t("dash.show")}
                      </button>
                      <CopyButton value={channel.rtmps_key} />
                    </>
                  )}
                </div>
              </Field>

              <Field label={t("dash.hlsUrl")}>
                <code className="break-all text-neutral-300">
                  {channel.hls_playback_url || "—"}
                </code>
              </Field>

              <div className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-4 text-sm text-neutral-300">
                <p className="mb-2 font-semibold text-neutral-100">{t("dash.obsTitle")}</p>
                <ol className="list-inside list-decimal space-y-1 text-neutral-400">
                  <li>{t("dash.obs1")}</li>
                  <li>{t("dash.obs2")}</li>
                  <li>{t("dash.obs3")}</li>
                  <li>{t("dash.obs4")}</li>
                </ol>
              </div>

              <button
                type="button"
                onClick={rotate}
                disabled={rotating}
                className="rounded-lg bg-amber-500 px-4 py-2 font-semibold text-neutral-950 hover:bg-amber-400 disabled:opacity-50"
              >
                {rotating ? t("dash.rotating") : t("dash.rotateKey")}
              </button>
              <p className="text-xs text-neutral-500">{t("dash.rotateWarn")}</p>

              <div className="space-y-3 rounded-xl border border-fuchsia-500/30 bg-fuchsia-500/5 p-4">
                <p className="font-semibold text-fuchsia-300">{t("dash.subTitle")}</p>
                <p className="text-xs text-neutral-400">{t("dash.subDesc")}</p>
                <Field label={t("dash.subPrice")}>
                  <input
                    type="number"
                    min={1}
                    value={tierPrice}
                    onChange={(e) => setTierPrice(e.target.value)}
                    className="w-40 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-fuchsia-500"
                  />
                </Field>
                <Field label={t("dash.subPerks")}>
                  <textarea
                    value={tierPerks}
                    onChange={(e) => setTierPerks(e.target.value)}
                    rows={3}
                    placeholder={"Badge abonné\nStickers exclusifs"}
                    className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-fuchsia-500"
                  />
                </Field>
                <label className="flex items-center gap-2 text-sm text-neutral-300">
                  <input
                    type="checkbox"
                    checked={tierActive}
                    onChange={(e) => setTierActive(e.target.checked)}
                    className="h-4 w-4 accent-fuchsia-500"
                  />
                  {t("dash.subOpen")}
                </label>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={saveTier}
                    disabled={tierSaving}
                    className="rounded-lg bg-fuchsia-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-fuchsia-400 disabled:opacity-50"
                  >
                    {tierSaving ? t("common.saving") : t("dash.subSave")}
                  </button>
                  {tierSaved && <span className="text-sm text-fuchsia-300">{t("common.saved")}</span>}
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <p className="font-semibold text-amber-300">{t("dash.accessRequired")}</p>
              <p className="mt-1 text-sm text-neutral-300">{t("dash.accessDesc")}</p>
              <Link
                href="/become-streamer"
                className="mt-3 inline-block rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
              >
                {t("dash.makeRequest")}
              </Link>
            </div>
          )}

          {channel.is_provisioned && stats && (
            <div className="grid grid-cols-3 gap-3 border-t border-neutral-800 pt-6">
              {[
                [t("dash.statsStreams"), stats.sessions_total],
                [t("dash.statsHours"), `${stats.broadcast_hours} h`],
                [t("dash.statsPeak"), stats.peak_viewers],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="rounded-lg border border-neutral-800 bg-neutral-900/40 p-3"
                >
                  <p className="text-xs uppercase tracking-wider text-neutral-500">
                    {label}
                  </p>
                  <p className="mt-1 text-xl font-bold">{value}</p>
                </div>
              ))}
            </div>
          )}

          {channel.is_provisioned && (
            <div className="border-t border-neutral-800 pt-6">
              <p className="mb-3 text-xs uppercase tracking-wider text-neutral-500">
                {t("dash.historyTitle")}
              </p>
              {sessions.length === 0 ? (
                <p className="text-sm text-neutral-500">{t("dash.noBroadcast")}</p>
              ) : (
                <table className="w-full text-left text-sm">
                  <thead className="text-xs uppercase tracking-wider text-neutral-500">
                    <tr>
                      <th className="pb-2">{t("dash.colDate")}</th>
                      <th className="pb-2">{t("dash.colDuration")}</th>
                      <th className="pb-2">{t("dash.colPeak")}</th>
                      <th className="pb-2">{t("dash.colCategory")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessions.map((s) => (
                      <tr key={s.started_at} className="border-t border-neutral-800/60">
                        <td className="py-2 text-neutral-300">
                          {new Date(s.started_at).toLocaleString("fr-FR", {
                            day: "2-digit",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </td>
                        <td className="py-2 text-neutral-300">
                          {formatDuration(s.duration_seconds, t)}
                        </td>
                        <td className="py-2 text-neutral-300">{s.peak_viewers}</td>
                        <td className="py-2 text-neutral-400">{s.category ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1 text-xs uppercase tracking-wider text-neutral-500">{label}</p>
      <div className="text-sm">{children}</div>
    </div>
  );
}
