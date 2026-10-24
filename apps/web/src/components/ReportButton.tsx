"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { Flag } from "lucide-react";

const REASONS = ["spam", "harassment", "hate", "other"] as const;

export function ReportButton({
  channelSlug,
  targetUsername,
  compact,
}: {
  channelSlug: string;
  targetUsername: string;
  /** Bouton icône seule (bandeau de la page chaîne). */
  compact?: boolean;
}) {
  const t = useT();
  const { user, authFetch } = useAuth();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("spam");
  const [details, setDetails] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) return null;
  if (done) return <span className="text-xs text-neutral-500">{t("report.done")}</span>;

  async function submit() {
    setError(null);
    try {
      await authFetch("/api/reports", {
        method: "POST",
        body: JSON.stringify({
          reason,
          channel_slug: channelSlug,
          target_username: targetUsername,
          details,
        }),
      });
      setDone(true);
      setOpen(false);
    } catch {
      setError(t("report.error"));
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        title={t("report.button")}
        aria-label={compact ? t("report.button") : undefined}
        className={
          compact
            ? "flex h-8 w-8 items-center justify-center rounded-md text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100"
            : "rounded-md border border-neutral-700 px-2 py-1 text-xs text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
        }
      >
        {compact ? <Flag size={18} aria-hidden /> : t("report.button")}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-64 space-y-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3 shadow-xl">
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-100 outline-none focus:border-secondary-light"
          >
            {REASONS.map((v) => (
              <option key={v} value={v}>
                {t(`report.reason.${v}`)}
              </option>
            ))}
          </select>
          <textarea
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            placeholder={t("report.details")}
            rows={2}
            maxLength={1000}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-100 outline-none focus:border-secondary-light"
          />
          {error && <p className="text-xs text-red-300">{error}</p>}
          <button
            type="button"
            onClick={submit}
            className="w-full rounded-lg bg-red-500/90 px-3 py-1.5 text-sm font-semibold text-neutral-950 hover:bg-red-400"
          >
            {t("report.submit")}
          </button>
        </div>
      )}
    </div>
  );
}
