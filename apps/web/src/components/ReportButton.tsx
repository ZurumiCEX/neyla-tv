"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";

const REASONS: [string, string][] = [
  ["spam", "Spam"],
  ["harassment", "Harcèlement"],
  ["hate", "Haine / discrimination"],
  ["other", "Autre"],
];

export function ReportButton({
  channelSlug,
  targetUsername,
}: {
  channelSlug: string;
  targetUsername: string;
}) {
  const { user, authFetch } = useAuth();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("spam");
  const [details, setDetails] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) return null;
  if (done) return <span className="text-xs text-neutral-500">Signalé ✓</span>;

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
      setError("Échec du signalement.");
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded-md border border-neutral-700 px-2 py-1 text-xs text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
      >
        Signaler
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-64 space-y-2 rounded-xl border border-neutral-800 bg-neutral-900 p-3 shadow-xl">
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-100 outline-none focus:border-emerald-500"
          >
            {REASONS.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
          <textarea
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            placeholder="Détails (optionnel)"
            rows={2}
            maxLength={1000}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-100 outline-none focus:border-emerald-500"
          />
          {error && <p className="text-xs text-red-300">{error}</p>}
          <button
            type="button"
            onClick={submit}
            className="w-full rounded-lg bg-red-500/90 px-3 py-1.5 text-sm font-semibold text-neutral-950 hover:bg-red-400"
          >
            Envoyer le signalement
          </button>
        </div>
      )}
    </div>
  );
}
