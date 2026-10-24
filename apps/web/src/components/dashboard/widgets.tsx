"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  BadgeInfo,
  ChevronRight,
  Gift,
  Heart,
  Pencil,
  RefreshCw,
  Shield,
  Sparkles,
  Star,
  ToggleRight,
  X,
} from "lucide-react";
import { Emoji } from "@/components/Emoji";
import {
  Panel,
  SettingRow,
  Stepper,
  Switch,
  inputCls,
  useDashboard,
  type Category,
} from "@/components/dashboard/kit";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

// ---------------------------------------------------------------- Réglages du chat

export type ChatSettings = {
  chat_followers_only: boolean;
  chat_follow_min_minutes: number;
  chat_subscribers_only: boolean;
  chat_emotes_only: boolean;
  chat_slow_seconds: number;
  chat_min_account_age_days: number;
  show_viewer_count: boolean;
  automod: Record<string, number | boolean>;
};

/** Lecture / écriture des réglages du chat (partagé par les widgets et la page Modération). */
export function useChatSettings() {
  const { authFetch } = useAuth();
  const [settings, setSettings] = useState<ChatSettings | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authFetch<ChatSettings>("/api/channels/me/chat-settings")
      .then(setSettings)
      .catch(() => setError("load"));
  }, [authFetch]);

  const patch = useCallback(
    async (changes: Partial<ChatSettings>) => {
      setSettings((s) => (s ? { ...s, ...changes } : s)); // optimiste
      try {
        setSettings(
          await authFetch<ChatSettings>("/api/channels/me/chat-settings", {
            method: "PATCH",
            body: JSON.stringify(changes),
          }),
        );
        setError(null);
        return true;
      } catch {
        setError("save");
        setSettings(await authFetch<ChatSettings>("/api/channels/me/chat-settings"));
        return false;
      }
    },
    [authFetch],
  );

  return { settings, patch, error };
}

export const SLOW_OPTIONS = [0, 3, 5, 10, 30, 60, 120] as const;
export const AGE_OPTIONS = [0, 1, 7, 30, 90] as const;
export const FOLLOW_MIN_OPTIONS = [0, 10, 60, 1440, 10080] as const;

export function useDurationLabels() {
  const t = useT();
  return {
    slow: (s: number) => (s === 0 ? t("dash2.off") : t("dash2.seconds", { n: s })),
    age: (d: number) => (d === 0 ? t("dash2.off") : t("dash2.days", { n: d })),
    followMin: (m: number) =>
      m === 0
        ? t("dash2.immediately")
        : m < 60
          ? t("dash2.minutes", { n: m })
          : m < 1440
            ? t("dash2.hours", { n: m / 60 })
            : t("dash2.days", { n: m / 1440 }),
  };
}

// ---------------------------------------------------------------- Session Info

export function SessionInfoPanel() {
  const t = useT();
  const { num } = useFormat();
  const { channel } = useDashboard();
  if (!channel) return null;
  const cells: [string, React.ReactNode][] = [
    [t("dash2.viewers"), channel.is_live ? num(channel.viewers ?? 0) : "—"],
    [t("dash2.followers"), num(channel.follower_count ?? 0)],
    [t("dash2.subCount"), num(channel.active_subs ?? 0)],
    [
      t("dash2.timeLive"),
      channel.is_live && channel.last_live_started_at ? (
        <LiveTimerInline startedAt={channel.last_live_started_at} />
      ) : (
        "—"
      ),
    ],
  ];
  return (
    <Panel title={t("dash2.sessionInfo")} icon={BadgeInfo} bodyClassName="p-0" expandable={false}>
      <div className="grid grid-cols-2 divide-neutral-800 sm:grid-cols-5 sm:divide-x">
        <div className="flex flex-col justify-center gap-1 px-4 py-3">
          <span
            className={`w-fit rounded px-2 py-0.5 text-xs font-black uppercase tracking-wider ${
              channel.is_live
                ? "bg-red-600 text-white"
                : "border border-neutral-500 text-neutral-200"
            }`}
          >
            {channel.is_live ? t("live.badge.on") : t("dash2.offline")}
          </span>
          <span className="text-xs text-neutral-500">{t("dash2.session")}</span>
        </div>
        {cells.map(([label, value]) => (
          <div key={label} className="flex flex-col justify-center gap-1 px-4 py-3">
            <span className="text-lg font-bold">{value}</span>
            <span className="text-xs text-neutral-500">{label}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function LiveTimerInline({ startedAt }: { startedAt: string }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (now === null) return <>—</>;
  const s = Math.max(0, Math.floor((now - new Date(startedAt).getTime()) / 1000));
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    <span className="tabular-nums">
      {pad(Math.floor(s / 3600))}:{pad(Math.floor((s % 3600) / 60))}:{pad(s % 60)}
    </span>
  );
}

// ---------------------------------------------------------------- Stream Info

export function StreamInfoPanel() {
  const t = useT();
  const { channel } = useDashboard();
  const [editing, setEditing] = useState(false);
  if (!channel) return null;
  return (
    <Panel
      title={t("dash2.streamInfo")}
      icon={BadgeInfo}
      actions={
        <button
          type="button"
          onClick={() => setEditing(true)}
          aria-label={t("dash2.edit")}
          title={t("dash2.edit")}
          className="flex h-7 w-7 items-center justify-center rounded-md text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
        >
          <Pencil size={15} />
        </button>
      }
    >
      <p className="font-bold">{channel.title || t("card.untitled")}</p>
      <p className="mt-1 text-sm font-semibold text-emerald-300">
        {channel.category?.name ?? t("dash2.noCategory")}
      </p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {channel.tags.map((tag) => (
          <span
            key={tag}
            className="rounded-full bg-neutral-800 px-2.5 py-0.5 text-xs text-neutral-300"
          >
            {tag}
          </span>
        ))}
      </div>
      {editing && <StreamInfoEditor onClose={() => setEditing(false)} />}
    </Panel>
  );
}

function StreamInfoEditor({ onClose }: { onClose: () => void }) {
  const t = useT();
  const { authFetch } = useAuth();
  const { channel, setChannel } = useDashboard();
  const [title, setTitle] = useState(channel?.title ?? "");
  const [category, setCategory] = useState(channel?.category?.slug ?? "");
  const [tags, setTags] = useState<string[]>(channel?.tags ?? []);
  const [tagInput, setTagInput] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<{ results: Category[] }>("/api/discover/categories?limit=50")
      .then((d) => setCategories(d.results))
      .catch(() => undefined);
  }, []);

  function addTag() {
    const tag = tagInput.trim().slice(0, 24);
    if (tag && !tags.includes(tag) && tags.length < 8) setTags([...tags, tag]);
    setTagInput("");
  }

  async function save() {
    setBusy(true);
    setError(null);
    try {
      setChannel(
        await authFetch("/api/channels/me", {
          method: "PATCH",
          body: JSON.stringify({ title, category_slug: category || null, tags }),
        }),
      );
      onClose();
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.saveError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-lg rounded-xl border border-neutral-800 bg-neutral-900 p-5 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold">{t("dash2.editStreamInfo")}</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label={t("common.close")}
            className="text-neutral-400 hover:text-neutral-100"
          >
            <X size={18} />
          </button>
        </div>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block font-semibold">{t("dash2.title")}</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={140}
            className={inputCls}
          />
        </label>
        <label className="mb-3 block text-sm">
          <span className="mb-1 block font-semibold">{t("dash2.category")}</span>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className={inputCls}
          >
            <option value="">—</option>
            {categories.map((c) => (
              <option key={c.slug} value={c.slug}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <div className="mb-4 text-sm">
          <span className="mb-1 block font-semibold">{t("dash2.tags")}</span>
          <div className="mb-2 flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => setTags(tags.filter((x) => x !== tag))}
                className="flex items-center gap-1 rounded-full bg-neutral-800 px-2.5 py-0.5 text-xs text-neutral-200 hover:bg-neutral-700"
              >
                {tag} <X size={12} />
              </button>
            ))}
          </div>
          <input
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addTag();
              }
            }}
            placeholder={t("dash2.tagPlaceholder")}
            className={inputCls}
          />
        </div>
        {error && <p className="mb-3 text-sm text-red-300">{error}</p>}
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm font-semibold text-neutral-300 hover:bg-neutral-800"
          >
            {t("dash2.cancel")}
          </button>
          <button
            type="button"
            onClick={save}
            disabled={busy}
            className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-bold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {busy ? t("common.saving") : t("dash2.save")}
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Channel Actions

export function ChannelActionsPanel() {
  const t = useT();
  const labels = useDurationLabels();
  const { settings, patch } = useChatSettings();
  return (
    <Panel title={t("dash2.channelActions")} icon={ToggleRight}>
      {!settings ? (
        <p className="text-sm text-neutral-500">{t("common.loading")}</p>
      ) : (
        <div className="divide-y divide-neutral-800">
          <div className="pb-2">
            <h3 className="mb-1 text-sm font-bold">{t("dash2.chatAccess")}</h3>
            <SettingRow label={t("dash2.accountAge")}>
              <Stepper
                label={t("dash2.accountAge")}
                value={settings.chat_min_account_age_days}
                options={AGE_OPTIONS as unknown as number[]}
                render={labels.age}
                onChange={(v) => patch({ chat_min_account_age_days: v })}
              />
            </SettingRow>
            <SettingRow label={t("dash2.followersOnly")}>
              <Switch
                label={t("dash2.followersOnly")}
                checked={settings.chat_followers_only}
                onChange={(v) => patch({ chat_followers_only: v })}
              />
            </SettingRow>
            <SettingRow label={t("dash2.subscribersOnly")}>
              <Switch
                label={t("dash2.subscribersOnly")}
                checked={settings.chat_subscribers_only}
                onChange={(v) => patch({ chat_subscribers_only: v })}
              />
            </SettingRow>
          </div>
          <div className="py-2">
            <h3 className="mb-1 text-sm font-bold">{t("dash2.chatOptions")}</h3>
            <SettingRow label={t("dash2.emotesOnly")}>
              <Switch
                label={t("dash2.emotesOnly")}
                checked={settings.chat_emotes_only}
                onChange={(v) => patch({ chat_emotes_only: v })}
              />
            </SettingRow>
            <SettingRow label={t("dash2.slowMode")}>
              <Stepper
                label={t("dash2.slowMode")}
                value={settings.chat_slow_seconds}
                options={SLOW_OPTIONS as unknown as number[]}
                render={labels.slow}
                onChange={(v) => patch({ chat_slow_seconds: v })}
              />
            </SettingRow>
            <Link
              href="/dashboard/moderation?tab=display"
              className="flex items-center justify-between py-2.5 text-sm font-semibold hover:text-emerald-300"
            >
              {t("dash2.bannedWords")} <ChevronRight size={16} />
            </Link>
            <Link
              href="/dashboard/moderation"
              className="flex items-center justify-between py-2.5 text-sm font-semibold hover:text-emerald-300"
            >
              {t("dash2.aiModeration")} <ChevronRight size={16} />
            </Link>
          </div>
          <div className="pt-2">
            <h3 className="mb-1 text-sm font-bold">{t("dash2.channelOptions")}</h3>
            <SettingRow label={t("dash2.showViewCount")}>
              <Switch
                label={t("dash2.showViewCount")}
                checked={settings.show_viewer_count}
                onChange={(v) => patch({ show_viewer_count: v })}
              />
            </SettingRow>
          </div>
        </div>
      )}
    </Panel>
  );
}

// ---------------------------------------------------------------- Activity Feed

type ActivityEvent = {
  type: "follow" | "tip" | "subscribe" | "resub" | "gift";
  actor: string;
  target?: string;
  amount?: number;
  message?: string;
  created_at: string;
};

const ACTIVITY_ICON = {
  follow: Heart,
  tip: Sparkles,
  subscribe: Star,
  resub: RefreshCw,
  gift: Gift,
};
const ACTIVITY_TONE = {
  follow: "text-emerald-300",
  tip: "text-sky-300",
  subscribe: "text-violet-300",
  resub: "text-violet-300",
  gift: "text-pink-300",
};

export function ActivityFeedPanel({ className = "" }: { className?: string }) {
  const t = useT();
  const { time, date } = useFormat();
  const { authFetch } = useAuth();
  const [items, setItems] = useState<ActivityEvent[] | null>(null);

  useEffect(() => {
    const load = () =>
      authFetch<{ results: ActivityEvent[] }>("/api/channels/me/activity?limit=40")
        .then((d) => setItems(d.results))
        .catch(() => setItems((v) => v ?? []));
    load();
    const id = setInterval(() => document.visibilityState === "visible" && load(), 10_000);
    return () => clearInterval(id);
  }, [authFetch]);

  return (
    <Panel
      title={t("dash2.activityFeed")}
      icon={Activity}
      className={className}
      bodyClassName="p-0"
    >
      {items === null ? (
        <p className="p-4 text-sm text-neutral-500">{t("common.loading")}</p>
      ) : items.length === 0 ? (
        <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center text-sm text-neutral-500">
          <Emoji emoji="🎉" size={36} />
          {t("dash.activityNone")}
        </div>
      ) : (
        <ul className="divide-y divide-neutral-800/70">
          {items.map((e, i) => {
            const Icon = ACTIVITY_ICON[e.type] ?? Activity;
            return (
              <li
                key={`${e.type}-${e.created_at}-${i}`}
                className="flex items-start gap-3 px-4 py-2.5 text-sm"
              >
                <Icon
                  size={16}
                  className={`mt-0.5 shrink-0 ${ACTIVITY_TONE[e.type] ?? ""}`}
                  aria-hidden
                />
                <div className="min-w-0 flex-1">
                  <p>
                    <span className="font-bold">{e.actor}</span>{" "}
                    <span className="text-neutral-400">
                      {t(`dash2.act.${e.type}`, { n: e.amount ?? 0, target: e.target ?? "" })}
                    </span>
                  </p>
                  {e.message && (
                    <p className="truncate text-xs text-neutral-500">« {e.message} »</p>
                  )}
                </div>
                <span className="shrink-0 text-xs text-neutral-500">
                  {date(e.created_at, { day: "2-digit", month: "short" })} {time(e.created_at)}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </Panel>
  );
}

// ---------------------------------------------------------------- Mod Actions

type ModActionRow = {
  id: number;
  action: string;
  actor: { username: string; display_name: string } | null;
  target: { username: string; display_name: string } | null;
  duration_s: number;
  detail: string;
  created_at: string;
};

export function ModActionsPanel({ className = "" }: { className?: string }) {
  const t = useT();
  const { time, date } = useFormat();
  const { authFetch } = useAuth();
  const [items, setItems] = useState<ModActionRow[] | null>(null);

  useEffect(() => {
    const load = () =>
      authFetch<{ results: ModActionRow[] }>("/api/channels/me/mod-actions?limit=40")
        .then((d) => setItems(d.results))
        .catch(() => setItems((v) => v ?? []));
    load();
    const id = setInterval(() => document.visibilityState === "visible" && load(), 15_000);
    return () => clearInterval(id);
  }, [authFetch]);

  return (
    <Panel title={t("dash2.modActions")} icon={Shield} className={className} bodyClassName="p-0">
      {items === null ? (
        <p className="p-4 text-sm text-neutral-500">{t("common.loading")}</p>
      ) : items.length === 0 ? (
        <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center text-sm text-neutral-500">
          <Emoji emoji="✅" size={32} />
          {t("dash2.noModActions")}
        </div>
      ) : (
        <ul className="divide-y divide-neutral-800/70">
          {items.map((a) => (
            <li key={a.id} className="px-4 py-2.5 text-sm">
              <p>
                <span className="font-bold">
                  {a.actor ? a.actor.display_name : t("dash2.autoMod")}
                </span>{" "}
                <span className="text-neutral-400">{t(`dash2.mod.${a.action}`)}</span>{" "}
                {a.target && <span className="font-semibold">@{a.target.username}</span>}
                {a.duration_s > 0 && (
                  <span className="text-neutral-500"> · {Math.round(a.duration_s / 60)} min</span>
                )}
              </p>
              <p className="truncate text-xs text-neutral-500">
                {date(a.created_at, { day: "2-digit", month: "short" })} {time(a.created_at)}
                {a.detail
                  ? ` · ${
                      a.action === "settings"
                        ? a.detail
                            .split(", ")
                            .map((f) => t(`dash2.field.${f}`))
                            .join(", ")
                        : a.detail
                    }`
                  : ""}
              </p>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
