"use client";

import { useState } from "react";
import { Clapperboard, Layers } from "lucide-react";
import { CopyButton } from "@/components/CopyButton";
import { ShortsManager } from "@/components/ShortsManager";
import { Panel, useDashboard } from "@/components/dashboard/kit";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

export default function DashboardStudioPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const { channel, setChannel } = useDashboard();
  const [sent, setSent] = useState<string | null>(null);
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  if (!channel) return <p className="text-neutral-500">{t("common.loading")}</p>;
  if (!channel.is_provisioned) return null;

  const overlay = `${origin}/overlay/${channel.overlay_token}`;
  async function test(kind: "follow" | "tip" | "subscribe") {
    try {
      await authFetch("/api/channels/me/overlay/test", {
        method: "POST",
        body: JSON.stringify({ kind }),
      });
      setSent(kind);
      setTimeout(() => setSent(null), 1500);
    } catch {
      setSent("error");
    }
  }
  async function regen() {
    if (!window.confirm(t("dash2.overlayRegenConfirm"))) return;
    const data = await authFetch<{ overlay_token: string }>("/api/channels/me/overlay/token", {
      method: "POST",
    }).catch(() => null);
    if (data) setChannel({ ...channel!, overlay_token: data.overlay_token });
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4">
      <Panel title={t("dash.overlayTitle")} icon={Layers} expandable={false}>
        <p className="mb-3 text-sm text-neutral-400">{t("dash.overlayDesc")}</p>
        {[
          [t("dash2.overlayAlerts"), overlay],
          [t("dash2.overlayChat"), `${overlay}/chat`],
          [t("dash2.overlayGoal"), `${overlay}/goal`],
        ].map(([label, url]) => (
          <div key={label} className="mb-2">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-neutral-500">
              {label}
            </p>
            <div className="flex items-center gap-2">
              <code className="min-w-0 flex-1 truncate rounded-md border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm">
                {url}
              </code>
              <CopyButton value={url} />
            </div>
          </div>
        ))}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-sm text-neutral-400">{t("dash.overlayTest")} :</span>
          {(["follow", "subscribe", "tip"] as const).map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => test(k)}
              className="rounded-md border border-neutral-700 px-3 py-1.5 text-sm font-semibold hover:border-emerald-500"
            >
              {t(`dash.alert${k === "follow" ? "Follow" : k === "subscribe" ? "Sub" : "Tip"}`)}
            </button>
          ))}
          {sent && sent !== "error" && <span className="text-sm text-green-400">✓</span>}
          <button
            type="button"
            onClick={regen}
            className="ml-auto rounded-md border border-amber-500/40 px-3 py-1.5 text-sm text-amber-300 hover:bg-amber-500/10"
          >
            {t("dash.overlayRegen")}
          </button>
        </div>
      </Panel>
      <Panel title={t("dash.tab.shorts")} icon={Clapperboard} expandable={false}>
        <ShortsManager />
      </Panel>
    </div>
  );
}
