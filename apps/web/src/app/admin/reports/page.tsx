"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Report = {
  id: number;
  reason: string;
  status: string;
  reporter: string;
  target_user: string | null;
  channel: string | null;
  details: string;
  resolution: string;
  created_at: string;
};

type Page = { count: number; results: Report[] };

const STATUSES = [
  { value: "", key: "admin.rstatus.all" },
  { value: "open", key: "admin.rstatus.open" },
  { value: "reviewed", key: "admin.rstatus.reviewed" },
  { value: "actioned", key: "admin.rstatus.actioned" },
  { value: "dismissed", key: "admin.rstatus.dismissed" },
];

export default function AdminReportsPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const [rows, setRows] = useState<Report[]>([]);
  const [statusFilter, setStatusFilter] = useState("open");
  const [error, setError] = useState<string | null>(null);
  const [words, setWords] = useState("");
  const [importMsg, setImportMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    try {
      const data = await authFetch<Page>(`/api/moderation/reports?${params.toString()}`);
      setRows(data.results);
    } catch {
      setError(t("common.loadError"));
    }
  }, [authFetch, statusFilter, t]);

  useEffect(() => {
    load();
  }, [load]);

  async function act(id: number, body: Record<string, unknown>) {
    try {
      await authFetch(`/api/moderation/reports/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      load();
    } catch {
      setError(t("admin.actionError"));
    }
  }

  async function importWords() {
    setImportMsg(null);
    try {
      const res = await authFetch<{ added: number; skipped: number }>(
        "/api/moderation/banned-words/import",
        { method: "POST", body: JSON.stringify({ words }) },
      );
      setImportMsg(t("admin.reports.importResult", { added: res.added, skipped: res.skipped }));
      setWords("");
    } catch {
      setImportMsg(t("admin.reports.importError"));
    }
  }

  return (
    <div className="space-y-8">
      <section>
        <div className="mb-4 flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm"
          >
            {STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {t(s.key)}
              </option>
            ))}
          </select>
        </div>

        {error && <p className="mb-3 text-sm text-red-300">{error}</p>}

        <ul className="space-y-3">
          {rows.map((r) => (
            <li key={r.id} className="rounded-xl border border-neutral-800 bg-neutral-900/40 p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="text-sm">
                  <p>
                    <span className="font-semibold capitalize">{r.reason}</span> ·{" "}
                    <span className="text-neutral-400">{r.status}</span>
                  </p>
                  <p className="mt-1 text-neutral-400">
                    {t("admin.reports.by")} @{r.reporter}
                    {r.target_user && <> · {t("admin.reports.target")} @{r.target_user}</>}
                    {r.channel && <> · {t("admin.reports.channel")} @{r.channel}</>}
                  </p>
                  {r.details && <p className="mt-1 text-neutral-300">{r.details}</p>}
                </div>
                <div className="flex shrink-0 flex-col gap-2">
                  <button
                    type="button"
                    onClick={() => act(r.id, { status: "dismissed", assign_to_self: true })}
                    className="rounded bg-neutral-700 px-2 py-1 text-xs font-semibold hover:bg-neutral-600"
                  >
                    {t("admin.reports.reject")}
                  </button>
                  {r.target_user && r.channel && (
                    <button
                      type="button"
                      onClick={() => act(r.id, { ban: true })}
                      className="rounded bg-red-500/80 px-2 py-1 text-xs font-semibold text-neutral-950 hover:bg-red-400"
                    >
                      {t("admin.reports.banClose")}
                    </button>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
        {rows.length === 0 && !error && (
          <p className="text-sm text-neutral-500">{t("admin.reports.empty")}</p>
        )}
      </section>

      <section className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
        <h2 className="mb-2 text-lg font-bold">{t("admin.reports.importTitle")}</h2>
        <p className="mb-2 text-xs text-neutral-400">{t("admin.reports.importDesc")}</p>
        <textarea
          value={words}
          onChange={(e) => setWords(e.target.value)}
          rows={4}
          placeholder="insulte1, insulte2&#10;insulte3"
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
        />
        <div className="mt-2 flex items-center gap-3">
          <button
            type="button"
            onClick={importWords}
            disabled={!words.trim()}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {t("admin.reports.import")}
          </button>
          {importMsg && <span className="text-sm text-neutral-400">{importMsg}</span>}
        </div>
      </section>
    </div>
  );
}
