"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Application = {
  status: "none" | "pending" | "under_review" | "interview" | "approved" | "rejected";
  rejection_reason?: string;
};

type Platforms = {
  twitch: string;
  youtube: string;
  tiktok: string;
  kick: string;
  facebook: string;
  discord: string;
};

type FormState = {
  full_name: string;
  country: string;
  primary_language: string;
  main_games: string;
  content_categories: string[];
  motivation: string;
  goals: string[];
  community_type: string[];
  has_streamed: boolean;
  platforms: Platforms;
  community_size: string;
  frequency: string;
  avg_duration: string;
  setup: string[];
  connection_quality: string;
  why_select: string;
  what_bring: string;
  intro_video_url: string;
  setup_screenshot_url: string;
  rules_accepted: boolean;
};

const EMPTY: FormState = {
  full_name: "",
  country: "",
  primary_language: "",
  main_games: "",
  content_categories: [],
  motivation: "",
  goals: [],
  community_type: [],
  has_streamed: false,
  platforms: { twitch: "", youtube: "", tiktok: "", kick: "", facebook: "", discord: "" },
  community_size: "",
  frequency: "",
  avg_duration: "",
  setup: [],
  connection_quality: "",
  why_select: "",
  what_bring: "",
  intro_video_url: "",
  setup_screenshot_url: "",
  rules_accepted: false,
};

const CONTENT = ["gaming", "just_chatting", "esports", "mobile", "irl", "creative"];
const GOALS = ["community", "entertain", "pro", "esport", "revenue", "passion"];
const COMMUNITY_TYPE = ["fun", "competitive", "chill", "educational", "esport", "african", "inclusive"];
const SETUP = ["pc", "console", "mobile", "webcam", "microphone", "stable_net"];
const SIZES = ["none", "under_100", "100_1k", "1k_10k", "10k_plus"];
const FREQ = ["occasional", "1_2_week", "3_5_week", "daily"];
const DUR = ["under_1h", "1_3h", "3_5h", "5h_plus"];
const CONN = ["low", "medium", "good", "excellent"];
const PLATFORM_KEYS: (keyof Platforms)[] = ["twitch", "youtube", "tiktok", "kick", "facebook", "discord"];

const TOTAL_STEPS = 5;

export default function BecomeStreamerPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [application, setApplication] = useState<Application | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setApplication(await authFetch<Application>("/api/streamer/application"));
    } catch {
      setApplication({ status: "none" });
    }
  }, [authFetch]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [loading, user, load, router]);

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }
  function toggle(key: "content_categories" | "goals" | "community_type" | "setup", value: string) {
    setForm((f) => {
      const arr = f[key];
      return { ...f, [key]: arr.includes(value) ? arr.filter((x) => x !== value) : [...arr, value] };
    });
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const data = await authFetch<Application>("/api/streamer/apply", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setApplication(data);
      setForm(EMPTY);
      setStep(1);
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("bs.submitError"));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !application) {
    return <main className="p-8 text-neutral-500">{t("common.loading")}</main>;
  }

  if (application.status === "approved") {
    return (
      <Shell t={t}>
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6">
          <p className="font-semibold text-emerald-300">{t("bs.approvedTitle")}</p>
          <p className="mt-1 text-sm text-neutral-300">{t("bs.approvedDesc")}</p>
          <Link
            href="/dashboard"
            className="mt-3 inline-block rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
          >
            {t("bs.openDashboard")}
          </Link>
        </div>
      </Shell>
    );
  }
  if (["pending", "under_review", "interview"].includes(application.status)) {
    const key =
      application.status === "interview"
        ? "bsf.state.interview"
        : application.status === "under_review"
          ? "bsf.state.review"
          : "bs.pendingDesc";
    return (
      <Shell t={t}>
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-6">
          <p className="font-semibold text-amber-300">{t("bs.pendingTitle")}</p>
          <p className="mt-1 text-sm text-neutral-300">{t(key)}</p>
        </div>
      </Shell>
    );
  }

  const pct = Math.round((step / TOTAL_STEPS) * 100);

  return (
    <Shell t={t}>
      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}
      {application.status === "rejected" && (
        <p className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
          {t("bs.rejected")}
          {application.rejection_reason ? ` ${application.rejection_reason}` : ""} {t("bs.canRetry")}
        </p>
      )}

      {/* Barre de progression */}
      <div className="mb-6">
        <div className="mb-2 flex items-center justify-between text-xs text-neutral-400">
          <span>{t(`bsf.step${step}.title`)}</span>
          <span>{t("bsf.progress", { step: String(step), total: String(TOTAL_STEPS) })}</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-800">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <section className="space-y-5 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
        {step === 1 && (
          <>
            <StepHead t={t} icon="👤" k="bsf.step1.title" desc="bsf.step1.desc" />
            <Field label={t("bsf.fullName")} value={form.full_name} onChange={(v) => set("full_name", v)} />
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={t("bsf.country")} value={form.country} onChange={(v) => set("country", v.toUpperCase())} maxLength={2} placeholder="CI, SN, FR…" />
              <Field label={t("bsf.language")} value={form.primary_language} onChange={(v) => set("primary_language", v)} placeholder={t("bsf.languagePh")} />
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <StepHead t={t} icon="🎮" k="bsf.step2.title" desc="bsf.step2.desc" />
            <Field label={t("bsf.mainGames")} value={form.main_games} onChange={(v) => set("main_games", v)} placeholder={t("bsf.mainGamesPh")} />
            <CheckGroup t={t} label={t("bsf.categories")} ns="content" options={CONTENT} selected={form.content_categories} onToggle={(v) => toggle("content_categories", v)} />
          </>
        )}

        {step === 3 && (
          <>
            <StepHead t={t} icon="✨" k="bsf.step3.title" desc="bsf.step3.desc" />
            <label className="block">
              <span className="mb-1 block text-sm text-neutral-300">{t("bsf.motivation")}</span>
              <textarea
                value={form.motivation}
                onChange={(e) => set("motivation", e.target.value)}
                maxLength={2000}
                rows={5}
                placeholder={t("bsf.motivationPh")}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
              />
            </label>
            <CheckGroup t={t} label={t("bsf.goals")} ns="goal" options={GOALS} selected={form.goals} onToggle={(v) => toggle("goals", v)} />
            <CheckGroup t={t} label={t("bsf.communityType")} ns="ctype" options={COMMUNITY_TYPE} selected={form.community_type} onToggle={(v) => toggle("community_type", v)} />
          </>
        )}

        {step === 4 && (
          <>
            <StepHead t={t} icon="📹" k="bsf.step4.title" desc="bsf.step4.desc" />
            <div>
              <span className="mb-1 block text-sm text-neutral-300">{t("bsf.hasStreamed")}</span>
              <div className="flex gap-2">
                {[true, false].map((val) => (
                  <button
                    key={String(val)}
                    type="button"
                    onClick={() => set("has_streamed", val)}
                    className={`rounded-lg border px-4 py-2 text-sm ${
                      form.has_streamed === val
                        ? "border-emerald-500 bg-emerald-500/15 text-emerald-300"
                        : "border-neutral-700 text-neutral-300 hover:border-neutral-500"
                    }`}
                  >
                    {val ? t("bsf.yes") : t("bsf.no")}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {PLATFORM_KEYS.map((p) => (
                <Field
                  key={p}
                  label={t(`bsf.platform.${p}`)}
                  value={form.platforms[p]}
                  onChange={(v) => set("platforms", { ...form.platforms, [p]: v })}
                  placeholder={t("bsf.platformPh")}
                />
              ))}
            </div>
            <Select t={t} label={t("bsf.communitySize")} ns="size" options={SIZES} value={form.community_size} onChange={(v) => set("community_size", v)} />
            <div className="grid gap-4 sm:grid-cols-2">
              <Select t={t} label={t("bsf.frequency")} ns="freq" options={FREQ} value={form.frequency} onChange={(v) => set("frequency", v)} />
              <Select t={t} label={t("bsf.duration")} ns="dur" options={DUR} value={form.avg_duration} onChange={(v) => set("avg_duration", v)} />
            </div>
            <CheckGroup t={t} label={t("bsf.setup")} ns="setup" options={SETUP} selected={form.setup} onToggle={(v) => toggle("setup", v)} />
            <Select t={t} label={t("bsf.connection")} ns="conn" options={CONN} value={form.connection_quality} onChange={(v) => set("connection_quality", v)} />
          </>
        )}

        {step === 5 && (
          <>
            <StepHead t={t} icon="🚀" k="bsf.step5.title" desc="bsf.step5.desc" />
            <Area label={t("bsf.whySelect")} value={form.why_select} onChange={(v) => set("why_select", v)} ph={t("bsf.whySelectPh")} />
            <Area label={t("bsf.whatBring")} value={form.what_bring} onChange={(v) => set("what_bring", v)} ph={t("bsf.whatBringPh")} />
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label={t("bsf.introVideo")} value={form.intro_video_url} onChange={(v) => set("intro_video_url", v)} placeholder="https://…" />
              <Field label={t("bsf.screenshot")} value={form.setup_screenshot_url} onChange={(v) => set("setup_screenshot_url", v)} placeholder="https://…" />
            </div>
            <label className="flex items-start gap-2 rounded-lg border border-neutral-800 bg-neutral-900 p-3 text-sm text-neutral-200">
              <input
                type="checkbox"
                checked={form.rules_accepted}
                onChange={(e) => set("rules_accepted", e.target.checked)}
                className="mt-0.5 h-4 w-4 cursor-pointer accent-emerald-500"
              />
              <span>{t("bsf.rules")}</span>
            </label>
          </>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={() => setStep((s) => Math.max(1, s - 1))}
            disabled={step === 1}
            className="rounded-lg border border-neutral-700 px-4 py-2 text-sm text-neutral-300 hover:border-neutral-500 disabled:opacity-40"
          >
            {t("bsf.back")}
          </button>
          {step < TOTAL_STEPS ? (
            <button
              type="button"
              onClick={() => setStep((s) => Math.min(TOTAL_STEPS, s + 1))}
              className="rounded-lg bg-emerald-500 px-5 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400"
            >
              {t("bsf.next")}
            </button>
          ) : (
            <button
              type="button"
              onClick={submit}
              disabled={submitting || !form.rules_accepted}
              className="rounded-lg bg-emerald-500 px-5 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
            >
              {submitting ? t("bs.submitting") : t("bs.submit")}
            </button>
          )}
        </div>
      </section>
    </Shell>
  );
}

function Shell({
  t,
  children,
}: {
  t: (k: string, p?: Record<string, string>) => string;
  children: React.ReactNode;
}) {
  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-1 text-2xl font-bold">{t("nav.becomeStreamer")}</h1>
      <p className="mb-6 text-sm text-neutral-400">{t("bsf.lead")}</p>
      {children}
    </main>
  );
}

function StepHead({
  t,
  icon,
  k,
  desc,
}: {
  t: (k: string) => string;
  icon: string;
  k: string;
  desc: string;
}) {
  return (
    <div>
      <h2 className="text-lg font-semibold">
        <span className="mr-2">{icon}</span>
        {t(k)}
      </h2>
      <p className="mt-0.5 text-sm text-neutral-400">{t(desc)}</p>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  maxLength,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  maxLength?: number;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm text-neutral-300">{label}</span>
      <input
        type="text"
        value={value}
        maxLength={maxLength}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
      />
    </label>
  );
}

function Area({
  label,
  value,
  onChange,
  ph,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  ph: string;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm text-neutral-300">{label}</span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        maxLength={1000}
        rows={3}
        placeholder={ph}
        className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
      />
    </label>
  );
}

function CheckGroup({
  t,
  label,
  ns,
  options,
  selected,
  onToggle,
}: {
  t: (k: string) => string;
  label: string;
  ns: string;
  options: string[];
  selected: string[];
  onToggle: (v: string) => void;
}) {
  return (
    <div>
      <span className="mb-2 block text-sm text-neutral-300">{label}</span>
      <div className="flex flex-wrap gap-2">
        {options.map((o) => {
          const on = selected.includes(o);
          return (
            <button
              key={o}
              type="button"
              onClick={() => onToggle(o)}
              className={`rounded-full border px-3 py-1.5 text-sm transition ${
                on
                  ? "border-emerald-500 bg-emerald-500/15 text-emerald-300"
                  : "border-neutral-700 text-neutral-300 hover:border-neutral-500"
              }`}
            >
              {t(`bsf.opt.${ns}.${o}`)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Select({
  t,
  label,
  ns,
  options,
  value,
  onChange,
}: {
  t: (k: string) => string;
  label: string;
  ns: string;
  options: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm text-neutral-300">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
      >
        <option value="">{t("bsf.choose")}</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {t(`bsf.opt.${ns}.${o}`)}
          </option>
        ))}
      </select>
    </label>
  );
}
