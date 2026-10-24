"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { X } from "lucide-react";
import { Avatar } from "@/components/Avatar";
import { SettingRow, Stepper, Switch, inputCls } from "@/components/dashboard/kit";
import {
  AGE_OPTIONS,
  FOLLOW_MIN_OPTIONS,
  SLOW_OPTIONS,
  useChatSettings,
  useDurationLabels,
} from "@/components/dashboard/widgets";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";

const CATEGORIES = ["sexual", "hate", "violence", "bullying", "drugs", "weapons"] as const;
const LEVELS = [0, 1, 2, 3] as const;
const PRESETS = { unfiltered: 0, minimal: 1, moderate: 2, maximum: 3 } as const;
type Preset = keyof typeof PRESETS | "custom";
type Tab = "message" | "access" | "display" | "unban";

function Card({ children }: { children: React.ReactNode }) {
  return (
    <section className="overflow-hidden rounded-lg border border-neutral-800 bg-neutral-900">
      {children}
    </section>
  );
}

export default function ModerationPage() {
  return (
    <Suspense>
      <ModerationTabs />
    </Suspense>
  );
}

function ModerationTabs() {
  const t = useT();
  const params = useSearchParams();
  const [tab, setTab] = useState<Tab>((params?.get("tab") as Tab) || "message");
  const tabs: Tab[] = ["message", "access", "display", "unban"];
  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-5 flex gap-1 overflow-x-auto border-b border-neutral-800">
        {tabs.map((id) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`-mb-px whitespace-nowrap border-b-2 px-3 py-2.5 text-[15px] font-bold transition ${
              tab === id
                ? "border-emerald-400 text-emerald-300"
                : "border-transparent text-neutral-200 hover:text-white"
            }`}
          >
            {t(`dash2.modTab.${id}`)}
          </button>
        ))}
      </div>
      {tab === "message" && <MessageModeration />}
      {tab === "access" && <AccessTab />}
      {tab === "display" && <DisplayTab />}
      {tab === "unban" && <UnbanRequests />}
    </div>
  );
}

function MessageModeration() {
  const t = useT();
  const { settings, patch } = useChatSettings();
  const [draft, setDraft] = useState<Record<string, number | boolean> | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings && !draft) setDraft({ ...settings.automod });
  }, [settings, draft]);

  const preset: Preset = useMemo(() => {
    if (!draft) return "custom";
    const levels = CATEGORIES.map((c) => Number(draft[c] ?? 0));
    const same = levels.every((l) => l === levels[0]);
    const found = Object.entries(PRESETS).find(([, v]) => v === levels[0]);
    return same && found ? (found[0] as Preset) : "custom";
  }, [draft]);

  if (!settings || !draft) return <p className="text-neutral-500">{t("common.loading")}</p>;

  const dirty = JSON.stringify(draft) !== JSON.stringify(settings.automod);
  const levelLabel = (l: number) => t(`dash2.level.${l}`);

  return (
    <Card>
      <div className="border-b border-neutral-800 p-5">
        <h2 className="text-lg font-bold">{t("dash2.aiModeration")}</h2>
        <p className="mt-1 text-sm text-neutral-400">{t("dash2.aiModerationDesc")}</p>
      </div>
      <div className="p-5">
        <p className="mb-3 text-sm">
          <span className="font-bold">{t("dash2.overallLevel")}</span>{" "}
          <span className="text-neutral-400">{t("dash2.overallHint")}</span>
        </p>
        <div className="mb-5 grid grid-cols-2 gap-1 rounded-md bg-neutral-950 p-1 sm:grid-cols-5">
          {(["unfiltered", "minimal", "moderate", "maximum", "custom"] as const).map((p) => (
            <button
              key={p}
              type="button"
              disabled={p === "custom"}
              onClick={() => {
                if (p === "custom") return;
                const next = { ...draft };
                for (const c of CATEGORIES) next[c] = PRESETS[p];
                setDraft(next);
                setSaved(false);
              }}
              className={`rounded px-3 py-2.5 text-sm font-bold transition ${
                preset === p
                  ? "bg-neutral-800 text-emerald-300"
                  : "text-neutral-200 hover:bg-neutral-800/60 disabled:cursor-default disabled:text-neutral-500"
              }`}
            >
              {t(`dash2.preset.${p}`)}
            </button>
          ))}
        </div>

        <div className="divide-y divide-neutral-800/70">
          {CATEGORIES.map((c) => (
            <SettingRow key={c} label={t(`dash2.cat.${c}`)} hint={t(`dash2.catHint.${c}`)}>
              <Stepper
                label={t(`dash2.cat.${c}`)}
                value={Number(draft[c] ?? 0)}
                options={LEVELS as unknown as number[]}
                render={levelLabel}
                onChange={(v) => {
                  setDraft({ ...draft, [c]: v });
                  setSaved(false);
                }}
              />
            </SettingRow>
          ))}
          {(["gibberish", "spam"] as const).map((k) => (
            <SettingRow key={k} label={t(`dash2.cat.${k}`)} hint={t(`dash2.catHint.${k}`)}>
              <Switch
                label={t(`dash2.cat.${k}`)}
                checked={Boolean(draft[k])}
                onChange={(v) => {
                  setDraft({ ...draft, [k]: v });
                  setSaved(false);
                }}
              />
            </SettingRow>
          ))}
        </div>

        <div className="mt-5 flex items-center justify-end gap-3">
          {saved && <span className="text-sm text-green-400">{t("common.saved")}</span>}
          <button
            type="button"
            disabled={!dirty}
            onClick={() => setDraft({ ...settings.automod })}
            className="px-3 py-2 text-sm font-semibold text-neutral-400 hover:text-neutral-100 disabled:opacity-40"
          >
            {t("dash2.cancel")}
          </button>
          <button
            type="button"
            disabled={!dirty}
            onClick={async () => {
              if (await patch({ automod: draft })) setSaved(true);
            }}
            className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-bold text-neutral-950 hover:bg-emerald-400 disabled:opacity-40"
          >
            {t("dash2.saveChanges")}
          </button>
        </div>
      </div>
    </Card>
  );
}

function AccessTab() {
  const t = useT();
  const labels = useDurationLabels();
  const { settings, patch } = useChatSettings();
  if (!settings) return <p className="text-neutral-500">{t("common.loading")}</p>;
  return (
    <Card>
      <div className="divide-y divide-neutral-800/70 p-5">
        <SettingRow label={t("dash2.followersOnly")} hint={t("dash2.followersOnlyHint")}>
          <Switch
            label={t("dash2.followersOnly")}
            checked={settings.chat_followers_only}
            onChange={(v) => patch({ chat_followers_only: v })}
          />
        </SettingRow>
        {settings.chat_followers_only && (
          <SettingRow label={t("dash2.followMin")} hint={t("dash2.followMinHint")}>
            <Stepper
              label={t("dash2.followMin")}
              value={settings.chat_follow_min_minutes}
              options={FOLLOW_MIN_OPTIONS as unknown as number[]}
              render={labels.followMin}
              onChange={(v) => patch({ chat_follow_min_minutes: v })}
            />
          </SettingRow>
        )}
        <SettingRow label={t("dash2.subscribersOnly")} hint={t("dash2.subscribersOnlyHint")}>
          <Switch
            label={t("dash2.subscribersOnly")}
            checked={settings.chat_subscribers_only}
            onChange={(v) => patch({ chat_subscribers_only: v })}
          />
        </SettingRow>
        <SettingRow label={t("dash2.accountAge")} hint={t("dash2.accountAgeHint")}>
          <Stepper
            label={t("dash2.accountAge")}
            value={settings.chat_min_account_age_days}
            options={AGE_OPTIONS as unknown as number[]}
            render={labels.age}
            onChange={(v) => patch({ chat_min_account_age_days: v })}
          />
        </SettingRow>
      </div>
    </Card>
  );
}

type Word = { id: number; word: string };

function DisplayTab() {
  const t = useT();
  const labels = useDurationLabels();
  const { authFetch } = useAuth();
  const { settings, patch } = useChatSettings();
  const [words, setWords] = useState<Word[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authFetch<{ results: Word[] }>("/api/channels/me/banned-words")
      .then((d) => setWords(d.results))
      .catch(() => undefined);
  }, [authFetch]);

  async function add() {
    if (!input.trim()) return;
    setError(null);
    try {
      const d = await authFetch<{ results: Word[] }>("/api/channels/me/banned-words", {
        method: "POST",
        body: JSON.stringify({ word: input }),
      });
      setWords(d.results);
      setInput("");
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.saveError"));
    }
  }

  async function remove(id: number) {
    await authFetch(`/api/channels/me/banned-words/${id}`, { method: "DELETE" }).catch(() => null);
    setWords((w) => w.filter((x) => x.id !== id));
  }

  if (!settings) return <p className="text-neutral-500">{t("common.loading")}</p>;
  return (
    <div className="space-y-4">
      <Card>
        <div className="divide-y divide-neutral-800/70 p-5">
          <SettingRow label={t("dash2.showViewCount")} hint={t("dash2.showViewCountHint")}>
            <Switch
              label={t("dash2.showViewCount")}
              checked={settings.show_viewer_count}
              onChange={(v) => patch({ show_viewer_count: v })}
            />
          </SettingRow>
          <SettingRow label={t("dash2.slowMode")} hint={t("dash2.slowModeHint")}>
            <Stepper
              label={t("dash2.slowMode")}
              value={settings.chat_slow_seconds}
              options={SLOW_OPTIONS as unknown as number[]}
              render={labels.slow}
              onChange={(v) => patch({ chat_slow_seconds: v })}
            />
          </SettingRow>
          <SettingRow label={t("dash2.emotesOnly")} hint={t("dash2.emotesOnlyHint")}>
            <Switch
              label={t("dash2.emotesOnly")}
              checked={settings.chat_emotes_only}
              onChange={(v) => patch({ chat_emotes_only: v })}
            />
          </SettingRow>
        </div>
      </Card>
      <Card>
        <div className="p-5">
          <h2 className="text-lg font-bold">{t("dash2.bannedWords")}</h2>
          <p className="mb-3 text-sm text-neutral-400">{t("dash2.bannedWordsDesc")}</p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              add();
            }}
            className="mb-3 flex gap-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              maxLength={60}
              placeholder={t("dash2.bannedWordPlaceholder")}
              className={inputCls}
            />
            <button
              type="submit"
              className="shrink-0 rounded-md bg-emerald-500 px-4 text-sm font-bold text-neutral-950 hover:bg-emerald-400"
            >
              {t("dash2.add")}
            </button>
          </form>
          {error && <p className="mb-2 text-sm text-red-300">{error}</p>}
          {words.length === 0 ? (
            <p className="text-sm text-neutral-500">{t("dash2.noBannedWords")}</p>
          ) : (
            <ul className="flex flex-wrap gap-2">
              {words.map((w) => (
                <li key={w.id}>
                  <button
                    type="button"
                    onClick={() => remove(w.id)}
                    title={t("dash2.remove")}
                    className="flex items-center gap-1.5 rounded-full bg-neutral-800 px-3 py-1 text-sm hover:bg-red-500/20 hover:text-red-200"
                  >
                    {w.word} <X size={13} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </Card>
    </div>
  );
}

type UnbanReq = {
  id: number;
  user: { username: string; display_name: string; avatar_url: string };
  message: string;
  status: string;
  created_at: string;
};

function UnbanRequests() {
  const t = useT();
  const { date } = useFormat();
  const { authFetch } = useAuth();
  const [status, setStatus] = useState<"pending" | "approved" | "denied">("pending");
  const [items, setItems] = useState<UnbanReq[] | null>(null);

  useEffect(() => {
    setItems(null);
    authFetch<{ results: UnbanReq[] }>(`/api/channels/me/unban-requests?status=${status}`)
      .then((d) => setItems(d.results))
      .catch(() => setItems([]));
  }, [authFetch, status]);

  async function decide(id: number, decision: "approve" | "deny") {
    await authFetch(`/api/channels/me/unban-requests/${id}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    }).catch(() => null);
    setItems((list) => (list ? list.filter((r) => r.id !== id) : list));
  }

  return (
    <Card>
      <div className="flex gap-2 border-b border-neutral-800 p-3">
        {(["pending", "approved", "denied"] as const).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStatus(s)}
            className={`rounded-md px-3 py-1.5 text-sm font-semibold ${
              status === s ? "bg-neutral-800 text-white" : "text-neutral-400 hover:text-neutral-100"
            }`}
          >
            {t(`dash2.unban.${s}`)}
          </button>
        ))}
      </div>
      {items === null ? (
        <p className="p-5 text-sm text-neutral-500">{t("common.loading")}</p>
      ) : items.length === 0 ? (
        <p className="p-5 text-sm text-neutral-500">{t("dash2.unban.none")}</p>
      ) : (
        <ul className="divide-y divide-neutral-800/70">
          {items.map((r) => (
            <li key={r.id} className="flex flex-wrap items-start gap-3 p-4">
              <Avatar src={r.user.avatar_url} name={r.user.display_name} size={36} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-bold">
                  {r.user.display_name}{" "}
                  <span className="font-normal text-neutral-500">
                    @{r.user.username} · {date(r.created_at, { day: "numeric", month: "short" })}
                  </span>
                </p>
                <p className="mt-1 whitespace-pre-line text-sm text-neutral-300">{r.message}</p>
              </div>
              {status === "pending" && (
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => decide(r.id, "deny")}
                    className="rounded-md border border-neutral-700 px-3 py-1.5 text-sm font-semibold hover:border-red-500/60 hover:text-red-300"
                  >
                    {t("dash2.unban.deny")}
                  </button>
                  <button
                    type="button"
                    onClick={() => decide(r.id, "approve")}
                    className="rounded-md bg-emerald-500 px-3 py-1.5 text-sm font-bold text-neutral-950 hover:bg-emerald-400"
                  >
                    {t("dash2.unban.approve")}
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
