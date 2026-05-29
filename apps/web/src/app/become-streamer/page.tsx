"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

type Application = {
  status: "none" | "pending" | "approved" | "rejected";
  motivation?: string;
  rejection_reason?: string;
};

export default function BecomeStreamerPage() {
  const router = useRouter();
  const t = useT();
  const { user, loading, authFetch } = useAuth();
  const [application, setApplication] = useState<Application | null>(null);
  const [motivation, setMotivation] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await authFetch<Application>("/api/streamer/application");
      setApplication(data);
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

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const data = await authFetch<Application>("/api/streamer/apply", {
        method: "POST",
        body: JSON.stringify({ motivation }),
      });
      setApplication(data);
      setMotivation("");
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

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-bold">{t("nav.becomeStreamer")}</h1>

      {error && (
        <p className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {application.status === "approved" ? (
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
      ) : application.status === "pending" ? (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-6">
          <p className="font-semibold text-amber-300">{t("bs.pendingTitle")}</p>
          <p className="mt-1 text-sm text-neutral-300">{t("bs.pendingDesc")}</p>
        </div>
      ) : (
        <section className="space-y-4 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
          {application.status === "rejected" && (
            <p className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
              {t("bs.rejected")}
              {application.rejection_reason ? ` ${application.rejection_reason}` : ""}{" "}
              {t("bs.canRetry")}
            </p>
          )}
          <p className="text-sm text-neutral-300">{t("bs.intro")}</p>
          <textarea
            value={motivation}
            onChange={(e) => setMotivation(e.target.value)}
            maxLength={1000}
            rows={4}
            placeholder={t("bs.placeholder")}
            className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
          />
          <button
            type="button"
            onClick={submit}
            disabled={submitting}
            className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            {submitting ? t("bs.submitting") : t("bs.submit")}
          </button>
        </section>
      )}
    </main>
  );
}
