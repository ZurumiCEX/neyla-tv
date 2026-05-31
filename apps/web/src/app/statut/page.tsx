"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useT } from "@/lib/i18n";

type ServiceStatus = { ok: boolean; latency_ms: number };
type StatusResp = {
  status: "ok" | "degraded";
  services: Record<string, ServiceStatus>;
  checked_at: string;
  uptime_pct_30d: number | null;
  incidents: { id: number; title: string; body_md: string; status: string }[];
};

const SERVICE_ORDER = ["api", "database", "redis", "cloudflare_stream"];

export default function StatusPage() {
  const t = useT();
  const [data, setData] = useState<StatusResp | null>(null);

  useEffect(() => {
    function refresh() {
      apiFetch<StatusResp>("/api/status")
        .then(setData)
        .catch(() => setData(null));
    }
    refresh();
    const id = setInterval(refresh, 30_000);
    return () => clearInterval(id);
  }, []);

  const allOk = data?.status === "ok";

  return (
    <main className="mx-auto max-w-3xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">{t("status.title")}</h1>
        <p className="mt-1 text-sm text-neutral-400">{t("status.subtitle")}</p>
      </header>

      <section
        className={`mb-6 rounded-2xl border p-5 ${
          data === null
            ? "border-neutral-800 bg-neutral-900"
            : allOk
              ? "border-emerald-500/40 bg-emerald-500/10"
              : "border-amber-500/40 bg-amber-500/10"
        }`}
      >
        <div className="flex items-center gap-3">
          <span
            className={`h-3 w-3 rounded-full ${
              data === null
                ? "bg-neutral-500"
                : allOk
                  ? "animate-pulse bg-emerald-400"
                  : "bg-amber-400"
            }`}
          />
          <p className="text-base font-semibold">
            {data === null
              ? t("common.loading")
              : allOk
                ? t("status.allGood")
                : t("status.degraded")}
          </p>
        </div>
        {data && (
          <p className="mt-2 text-xs text-neutral-400">
            {t("status.lastChecked", {
              time: new Date(data.checked_at).toLocaleTimeString("fr-FR"),
            })}
          </p>
        )}
      </section>

      <section className="space-y-2">
        {data &&
          SERVICE_ORDER.filter((k) => k in data.services).map((k) => {
            const s = data.services[k];
            return (
              <div
                key={k}
                className="flex items-center gap-3 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4"
              >
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    s.ok ? "bg-emerald-400" : "bg-red-400"
                  }`}
                />
                <span className="flex-1 text-sm font-medium text-neutral-200">
                  {t(`status.service.${k}`)}
                </span>
                <span className="font-mono text-xs text-neutral-500">
                  {s.latency_ms} ms
                </span>
              </div>
            );
          })}
      </section>

      {data && data.uptime_pct_30d !== null && (
        <p className="mt-6 text-sm text-neutral-400">
          {t("status.uptime30d")} : <span className="font-semibold text-neutral-100">{data.uptime_pct_30d}%</span>
        </p>
      )}
    </main>
  );
}
