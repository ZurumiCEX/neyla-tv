"use client";

import { useState } from "react";
import { Check, ChevronDown, Copy, Download, Eye, EyeOff, Info } from "lucide-react";
import { useDashboard } from "@/components/dashboard/kit";
import { StreamToolkit } from "@/components/StreamToolkit";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

// Réglages d'encodage conseillés (sortie OBS « Avancé »).
const ENCODING = {
  resolution: "1920×1080",
  fps: "60",
  rate: "CBR",
  bitrate: "6000",
  keyframe: "2",
};

function CopyIcon({ value }: { value: string }) {
  const t = useT();
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setDone(true);
          setTimeout(() => setDone(false), 1200);
        } catch {
          /* presse-papiers indisponible */
        }
      }}
      aria-label={t("dash2.copy")}
      title={t("dash2.copy")}
      className="flex h-8 w-8 items-center justify-center rounded-md text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
    >
      {done ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
    </button>
  );
}

function SecretField({ value, label }: { value: string; label: string }) {
  const t = useT();
  const [shown, setShown] = useState(false);
  return (
    <div className="flex items-center gap-1 rounded-md border border-neutral-700 bg-neutral-950 pl-3 pr-1">
      <input
        readOnly
        aria-label={label}
        type={shown ? "text" : "password"}
        value={value || "—"}
        className="h-10 min-w-0 flex-1 bg-transparent font-mono text-sm text-neutral-100 outline-none"
      />
      <button
        type="button"
        onClick={() => setShown((v) => !v)}
        aria-label={shown ? t("dash.hide") : t("dash.show")}
        title={shown ? t("dash.hide") : t("dash.show")}
        className="flex h-8 w-8 items-center justify-center rounded-md text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
      >
        {shown ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
      {value && <CopyIcon value={value} />}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="overflow-hidden rounded-lg border border-neutral-800 bg-neutral-900">
      <h2 className="border-b border-neutral-800 px-5 py-3.5 text-[17px] font-bold">{title}</h2>
      <div className="p-5">{children}</div>
    </section>
  );
}

export default function StreamKeyPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const { channel, setChannel, reload } = useDashboard();
  const [rotating, setRotating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [advanced, setAdvanced] = useState(false);
  const origin = typeof window !== "undefined" ? window.location.origin : "";

  if (!channel) return <p className="text-neutral-500">{t("common.loading")}</p>;
  if (!channel.is_provisioned) return null;

  async function rotate() {
    if (!window.confirm(t("dash.rotateConfirm"))) return;
    setRotating(true);
    setError(null);
    try {
      setChannel(await authFetch("/api/channels/me/key/rotate", { method: "POST" }));
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("dash.rotateError"));
    } finally {
      setRotating(false);
    }
  }

  function downloadObsProfile() {
    // Profil de service OBS (« Personnalisé ») + réglages conseillés, à importer.
    const profile = {
      settings: { server: channel!.ingest_url, key: channel!.stream_key, use_auth: false },
      type: "rtmp_custom",
      neyla_recommended: ENCODING,
    };
    const blob = new Blob([JSON.stringify(profile, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "neyla-obs-service.json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  const enc: [string, string, boolean][] = [
    [t("dash2.enc.resolution"), ENCODING.resolution, true],
    [t("dash2.enc.fps"), ENCODING.fps, true],
    [t("dash2.enc.rate"), ENCODING.rate, false],
    [t("dash2.enc.bitrate"), ENCODING.bitrate, true],
    [t("dash2.enc.keyframe"), ENCODING.keyframe, true],
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <h1 className="text-2xl font-bold">{t("dash2.nav.streamKey")}</h1>
      {error && (
        <p className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      <Card title={t("dash2.streamUrl")}>
        <SecretField value={channel.ingest_url} label={t("dash2.streamUrl")} />
      </Card>

      <Card title={t("dash.streamKey")}>
        <div className="flex gap-3">
          <div className="min-w-0 flex-1">
            <SecretField value={channel.stream_key} label={t("dash.streamKey")} />
          </div>
          <button
            type="button"
            onClick={rotate}
            disabled={rotating}
            className="h-10 shrink-0 rounded-md bg-neutral-800 px-4 text-sm font-bold hover:bg-neutral-700 disabled:opacity-50"
          >
            {rotating ? t("dash.rotating") : t("dash2.reset")}
          </button>
        </div>
        <p className="mt-2 text-xs text-neutral-500">{t("dash.rotateWarn")}</p>
      </Card>

      <Card title={t("dash2.encodingTitle")}>
        <p className="mb-4 text-sm text-neutral-400">{t("dash2.encodingDesc")}</p>
        <div className="grid gap-4 sm:grid-cols-2">
          {enc.map(([label, value, copyable]) => (
            <label key={label} className="block text-sm">
              <span className="mb-1 block font-semibold">{label}</span>
              <span className="flex items-center rounded-md border border-neutral-700 bg-neutral-950 pl-3 pr-1">
                <input
                  readOnly
                  value={value}
                  className="h-10 min-w-0 flex-1 bg-transparent text-sm outline-none"
                />
                {copyable && <CopyIcon value={value} />}
              </span>
            </label>
          ))}
        </div>
        <button
          type="button"
          onClick={downloadObsProfile}
          className="mt-5 flex items-center gap-2 text-sm font-bold hover:text-emerald-300"
        >
          <Download size={16} /> {t("dash2.downloadObs")}
          <span title={t("dash2.downloadObsHint")}>
            <Info size={14} className="text-neutral-500" />
          </span>
        </button>
      </Card>

      <section className="overflow-hidden rounded-lg border border-neutral-800 bg-neutral-900">
        <button
          type="button"
          onClick={() => setAdvanced((v) => !v)}
          aria-expanded={advanced}
          className="flex w-full items-center justify-between px-5 py-4 text-left"
        >
          <span>
            <span className="block text-[17px] font-bold">{t("dash2.advanced")}</span>
            <span className="text-sm text-neutral-400">{t("dash2.advancedDesc")}</span>
          </span>
          <ChevronDown size={20} className={`transition ${advanced ? "rotate-180" : ""}`} />
        </button>
        {advanced && (
          <div className="space-y-4 border-t border-neutral-800 p-5 text-sm">
            <div>
              <p className="mb-1 font-semibold">{t("dash.hlsUrl")}</p>
              <code className="break-all text-neutral-300">{channel.playback_url || "—"}</code>
            </div>
            <div className="rounded-md border border-neutral-800 bg-neutral-950/50 p-4">
              <p className="mb-2 font-semibold">{t("dash.obsTitle")}</p>
              <ol className="list-inside list-decimal space-y-1 text-neutral-400">
                <li>{t("dash.obs1")}</li>
                <li>{t("dash.obs2")}</li>
                <li>{t("dash.obs3")}</li>
                <li>{t("dash.obs4")}</li>
              </ol>
            </div>
            <StreamToolkit
              overlayToken={channel.overlay_token}
              origin={origin}
              goal={{
                goal_title: channel.goal_title ?? "",
                goal_kind: channel.goal_kind ?? "subs",
                goal_target: channel.goal_target ?? 0,
              }}
              onGoalSaved={reload}
            />
          </div>
        )}
      </section>
    </div>
  );
}
