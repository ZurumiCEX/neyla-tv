"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { ChatBansManager } from "@/components/ChatBansManager";
import { ChatPanel } from "@/components/ChatPanel";
import { CollaborationManager } from "@/components/CollaborationManager";
import { CopyButton } from "@/components/CopyButton";
import { HlsPlayer } from "@/components/HlsPlayer";
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
  tags: string[];
  overlay_token: string;
  collaborations_open: boolean;
  follower_count?: number;
  viewers?: number;
};

type ActivityEvent = {
  type: "follow" | "tip" | "subscribe";
  actor: string;
  amount?: number;
  message?: string;
  created_at: string;
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

type Tab =
  | "overview"
  | "audience"
  | "community"
  | "monetization"
  | "collaboration"
  | "broadcast";

function formatDuration(seconds: number | null, t: TFn): string {
  if (seconds === null) return t("dash.durationOngoing");
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h > 0 ? `${h}h${String(m).padStart(2, "0")}` : t("dash.durationMin", { m });
}

function SessionTimer({ startedAt }: { startedAt: string }) {
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((x) => x + 1), 1000);
    return () => clearInterval(id);
  }, []);
  const elapsed = Math.max(0, Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000));
  const h = Math.floor(elapsed / 3600);
  const m = Math.floor((elapsed % 3600) / 60);
  const s = elapsed % 60;
  return (
    <span className="font-mono tabular-nums">
      {h}:{String(m).padStart(2, "0")}:{String(s).padStart(2, "0")}
    </span>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [channel, setChannel] = useState<MyChannel | null>(null);
  const [sessions, setSessions] = useState<StreamSession[]>([]);
  const [stats, setStats] = useState<MyStats | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [rotating, setRotating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [revealKey, setRevealKey] = useState(false);
  const [liveBusy, setLiveBusy] = useState(false);

  const [title, setTitle] = useState("");
  const [categorySlug, setCategorySlug] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");

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
      setTags(data.tags ?? []);
      authFetch<{ results: ActivityEvent[] }>("/api/channels/me/activity")
        .then((d) => setActivity(d.results))
        .catch(() => undefined);
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
        body: JSON.stringify({ title, category_slug: categorySlug || null, tags }),
      });
      setChannel(data);
      setTags(data.tags ?? []);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.saveError"));
    } finally {
      setSaving(false);
    }
  }

  function addTag() {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !tags.includes(tag) && tags.length < 8) setTags([...tags, tag]);
    setTagInput("");
  }

  async function toggleLive(live: boolean) {
    setLiveBusy(true);
    try {
      const data = await authFetch<{ is_live: boolean }>("/api/channels/me/live", {
        method: "POST",
        body: JSON.stringify({ live }),
      });
      setChannel((c) =>
        c
          ? {
              ...c,
              is_live: data.is_live,
              last_live_started_at: data.is_live
                ? (c.last_live_started_at ?? new Date().toISOString())
                : c.last_live_started_at,
            }
          : c,
      );
    } catch {
      // ignore
    } finally {
      setLiveBusy(false);
    }
  }

  const [origin, setOrigin] = useState("");
  useEffect(() => {
    setOrigin(window.location.origin);
  }, []);

  async function regenOverlay() {
    try {
      const data = await authFetch<{ overlay_token: string }>("/api/channels/me/overlay/token", {
        method: "POST",
      });
      setChannel((c) => (c ? { ...c, overlay_token: data.overlay_token } : c));
    } catch {
      // ignore
    }
  }

  async function toggleCollabOpen() {
    if (!channel) return;
    const next = !channel.collaborations_open;
    setChannel((c) => (c ? { ...c, collaborations_open: next } : c));
    try {
      await authFetch("/api/channels/me", {
        method: "PATCH",
        body: JSON.stringify({ collaborations_open: next }),
      });
    } catch {
      setChannel((c) => (c ? { ...c, collaborations_open: !next } : c));
    }
  }

  async function testAlert(kind: "follow" | "tip" | "subscribe") {
    try {
      await authFetch("/api/channels/me/overlay/test", {
        method: "POST",
        body: JSON.stringify({ kind }),
      });
    } catch {
      // ignore
    }
  }

  async function rotate() {
    setRotating(true);
    try {
      const data = await authFetch<MyChannel>("/api/channels/me/key/rotate", { method: "POST" });
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
        body: JSON.stringify({ price_aura: Number(tierPrice) || 1, perks, is_active: tierActive }),
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

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: t("dash.tab.overview") },
    { id: "audience", label: t("dash.tab.audience") },
    { id: "community", label: t("dash.tab.community") },
    { id: "monetization", label: t("dash.tab.monetization") },
    { id: "collaboration", label: t("dash.tab.collaboration") },
    { id: "broadcast", label: t("dash.tab.broadcast") },
  ];

  const gated = channel && !channel.is_provisioned;

  return (
    <main className="mx-auto max-w-6xl p-4 sm:p-6">
      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {channel && (
        <>
          {/* Barre studio persistante */}
          <header className="mb-5 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 px-5 py-3">
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-bold">{t("dash.title")}</h1>
              <span className="text-neutral-500">@{channel.slug}</span>
              {channel.is_provisioned && (
                <LiveBadge slug={channel.slug} initial={{ is_live: channel.is_live }} />
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              {channel.is_live && channel.last_live_started_at && (
                <span className="flex items-center gap-1.5 text-neutral-400">
                  <span className="text-xs uppercase tracking-wider">{t("dash.session")}</span>
                  <SessionTimer startedAt={channel.last_live_started_at} />
                </span>
              )}
              <span className="text-neutral-400">
                <span className="font-semibold text-neutral-100">{channel.viewers ?? 0}</span>{" "}
                {t("dash.currentViewers")}
              </span>
              {channel.is_live ? (
                <button
                  type="button"
                  onClick={() => toggleLive(false)}
                  disabled={liveBusy}
                  className="rounded-lg border border-red-500/50 px-3 py-1.5 font-semibold text-red-300 hover:bg-red-500/10 disabled:opacity-50"
                >
                  {t("dash.endLive")}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => toggleLive(true)}
                  disabled={liveBusy}
                  className="rounded-lg bg-red-500 px-3 py-1.5 font-semibold text-neutral-950 hover:bg-red-400 disabled:opacity-50"
                >
                  {t("dash.goLive")}
                </button>
              )}
              <Link href={`/c/${channel.slug}`} className="text-emerald-300 underline">
                {t("dash.publicPage")}
              </Link>
            </div>
          </header>

          {gated && (
            <div className="mb-5 rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4">
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

          {/* Onglets */}
          <div className="mb-6 flex flex-wrap gap-1 border-b border-neutral-800">
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

          {/* APERÇU */}
          {tab === "overview" && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_400px]">
              <section className="space-y-4">
                <div className="overflow-hidden rounded-2xl border border-neutral-800 bg-black">
                  {channel.is_provisioned && channel.hls_playback_url ? (
                    <HlsPlayer
                      src={channel.hls_playback_url}
                      poster={channel.thumbnail_url}
                      className="aspect-video w-full"
                    />
                  ) : (
                    <div className="flex aspect-video w-full items-center justify-center text-sm text-neutral-600">
                      {channel.is_live ? t("dash.preview") : t("dash.disconnected")}
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Stat label={t("dash.followers")} value={channel.follower_count ?? 0} />
                  <Stat label={t("dash.currentViewers")} value={channel.viewers ?? 0} />
                </div>
              </section>

              <section className="space-y-3 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
                <h2 className="font-semibold">{t("dash.streamInfo")}</h2>
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
                <Field label={t("dash.tags")}>
                  <div className="flex flex-wrap items-center gap-2">
                    {tags.map((tag) => (
                      <span
                        key={tag}
                        className="flex items-center gap-1 rounded-full bg-neutral-800 px-2.5 py-1 text-xs text-neutral-200"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => setTags(tags.filter((x) => x !== tag))}
                          className="text-neutral-500 hover:text-red-300"
                          aria-label={`remove ${tag}`}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                    {tags.length < 8 && (
                      <input
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === ",") {
                            e.preventDefault();
                            addTag();
                          }
                        }}
                        onBlur={addTag}
                        maxLength={24}
                        placeholder={t("dash.tagsPlaceholder")}
                        className="min-w-[8rem] flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-1.5 text-sm text-neutral-100 outline-none focus:border-emerald-500"
                      />
                    )}
                  </div>
                </Field>
                <button
                  type="button"
                  onClick={save}
                  disabled={saving}
                  className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
                >
                  {saving ? t("common.saving") : t("common.save")}
                </button>
              </section>
            </div>
          )}

          {/* AUDIENCE */}
          {tab === "audience" && (
            <div className="space-y-6">
              {stats && (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <Stat label={t("dash.statsStreams")} value={stats.sessions_total} />
                  <Stat label={t("dash.statsHours")} value={`${stats.broadcast_hours} h`} />
                  <Stat label={t("dash.statsPeak")} value={stats.peak_viewers} />
                  <Stat label={t("dash.followers")} value={stats.follower_count} />
                </div>
              )}

              <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
                <h2 className="mb-3 font-semibold">{t("dash.activity")}</h2>
                {activity.length === 0 ? (
                  <p className="text-sm text-neutral-500">{t("dash.activityNone")}</p>
                ) : (
                  <ul className="space-y-2">
                    {activity.map((e, i) => (
                      <li
                        key={i}
                        className="flex items-center justify-between rounded-lg border border-neutral-800/60 bg-neutral-900/40 px-3 py-2 text-sm"
                      >
                        <span className="text-neutral-200">
                          <span className="font-semibold">{e.actor}</span>{" "}
                          <span className="text-neutral-400">
                            {e.type === "tip"
                              ? t("dash.act.tip", { n: e.amount ?? 0 })
                              : t(`dash.act.${e.type}`)}
                          </span>
                          {e.message ? <span className="text-neutral-500"> · {e.message}</span> : null}
                        </span>
                        <span className="shrink-0 text-xs text-neutral-600">
                          {new Date(e.created_at).toLocaleDateString("fr-FR", {
                            day: "2-digit",
                            month: "short",
                          })}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
                <h2 className="mb-3 font-semibold">{t("dash.historyTitle")}</h2>
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
              </section>
            </div>
          )}

          {/* COMMUNAUTÉ */}
          {tab === "community" && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_380px]">
              <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
                <ChatBansManager />
              </section>
              <section>
                <h2 className="mb-3 font-semibold">{t("dash.chatLive")}</h2>
                <ChatPanel slug={channel.slug} isLive={channel.is_live} />
              </section>
            </div>
          )}

          {/* MONÉTISATION */}
          {tab === "monetization" && (
            <div className="space-y-6">
              <section className="space-y-3 rounded-2xl border border-fuchsia-500/30 bg-fuchsia-500/5 p-5">
                <h2 className="font-semibold text-fuchsia-300">{t("dash.subTitle")}</h2>
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
              </section>

              <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
                <h2 className="font-semibold">{t("dash.payoutTitle")}</h2>
                <p className="mt-1 text-sm text-neutral-400">{t("dash.payoutDesc")}</p>
                <Link
                  href="/wallet"
                  className="mt-3 inline-block rounded-lg border border-neutral-700 px-4 py-2 text-sm font-semibold text-neutral-200 hover:border-emerald-500"
                >
                  {t("dash.payoutLink")}
                </Link>
              </section>
            </div>
          )}

          {/* COLLABORATION */}
          {tab === "collaboration" && (
            <div className="space-y-6">
              <section className="flex items-center justify-between rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
                <div>
                  <h2 className="font-semibold">{t("collab.openTitle")}</h2>
                  <p className="text-sm text-neutral-400">{t("collab.openDesc")}</p>
                </div>
                <button
                  type="button"
                  onClick={toggleCollabOpen}
                  role="switch"
                  aria-checked={channel.collaborations_open}
                  className={`relative h-6 w-11 shrink-0 rounded-full transition ${
                    channel.collaborations_open ? "bg-emerald-500" : "bg-neutral-700"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all ${
                      channel.collaborations_open ? "left-[22px]" : "left-0.5"
                    }`}
                  />
                </button>
              </section>
              <CollaborationManager />
            </div>
          )}

          {/* DIFFUSION */}
          {tab === "broadcast" &&
            (channel.is_provisioned ? (
              <section className="space-y-5 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
                <Field label={t("dash.status")}>
                  <span className="text-emerald-300">{t("dash.approved")}</span>
                </Field>
                <Field label={t("dash.rtmpsServer")}>
                  <div className="flex items-center gap-2">
                    <code className="break-all text-emerald-300">{channel.rtmps_url || "—"}</code>
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
                  <code className="break-all text-neutral-300">{channel.hls_playback_url || "—"}</code>
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
                <div>
                  <button
                    type="button"
                    onClick={rotate}
                    disabled={rotating}
                    className="rounded-lg bg-amber-500 px-4 py-2 font-semibold text-neutral-950 hover:bg-amber-400 disabled:opacity-50"
                  >
                    {rotating ? t("dash.rotating") : t("dash.rotateKey")}
                  </button>
                  <p className="mt-1 text-xs text-neutral-500">{t("dash.rotateWarn")}</p>
                </div>

                <div className="space-y-3 border-t border-neutral-800 pt-5">
                  <div>
                    <p className="font-semibold text-neutral-100">{t("dash.overlayTitle")}</p>
                    <p className="text-xs text-neutral-400">{t("dash.overlayDesc")}</p>
                  </div>
                  <Field label={t("dash.overlayUrl")}>
                    <div className="flex items-center gap-2">
                      <code className="break-all text-emerald-300">
                        {origin ? `${origin}/overlay/${channel.overlay_token}` : "…"}
                      </code>
                      {origin && channel.overlay_token && (
                        <CopyButton value={`${origin}/overlay/${channel.overlay_token}`} />
                      )}
                    </div>
                  </Field>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs text-neutral-500">{t("dash.overlayTest")} :</span>
                    <button
                      type="button"
                      onClick={() => testAlert("follow")}
                      className="rounded-lg border border-neutral-700 px-3 py-1 text-xs hover:border-emerald-500"
                    >
                      {t("dash.alertFollow")}
                    </button>
                    <button
                      type="button"
                      onClick={() => testAlert("subscribe")}
                      className="rounded-lg border border-neutral-700 px-3 py-1 text-xs hover:border-fuchsia-500"
                    >
                      {t("dash.alertSub")}
                    </button>
                    <button
                      type="button"
                      onClick={() => testAlert("tip")}
                      className="rounded-lg border border-neutral-700 px-3 py-1 text-xs hover:border-blue-500"
                    >
                      {t("dash.alertTip")}
                    </button>
                    <button
                      type="button"
                      onClick={regenOverlay}
                      className="ml-auto rounded-lg border border-amber-500/40 px-3 py-1 text-xs text-amber-300 hover:bg-amber-500/10"
                    >
                      {t("dash.overlayRegen")}
                    </button>
                  </div>
                </div>
              </section>
            ) : (
              <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4">
                <p className="font-semibold text-amber-300">{t("dash.accessRequired")}</p>
                <p className="mt-1 text-sm text-neutral-300">{t("dash.accessDesc")}</p>
                <Link
                  href="/become-streamer"
                  className="mt-3 inline-block rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
                >
                  {t("dash.makeRequest")}
                </Link>
              </div>
            ))}
        </>
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

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-4">
      <p className="text-xs uppercase tracking-wider text-neutral-500">{label}</p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
    </div>
  );
}
