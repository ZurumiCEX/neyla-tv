"use client";

// Onglet « Instant » du tableau de bord : publier des vidéos courtes (≤ 60 s)
// et suivre leur encodage / leurs statistiques.

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";
import { useFormat } from "@/lib/use-format";
import { type BunnyUpload, tusUpload, videoDuration } from "@/lib/tus-upload";

type MyShort = {
  id: number;
  title: string;
  status: "uploading" | "processing" | "ready" | "failed";
  thumbnail_url: string;
  duration_s: number;
  view_count: number;
  like_count: number;
  is_published: boolean;
  created_at: string;
};

type CreateResp = {
  short: MyShort;
  upload: ({ mode: "tus" } & BunnyUpload) | { mode: "fake" };
};

const MAX_DURATION_S = 60;
const MAX_SIZE_MB = 200;

export function ShortsManager() {
  const t = useT();
  const { num, date } = useFormat();
  const { authFetch } = useAuth();
  const [shorts, setShorts] = useState<MyShort[] | null>(null);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const load = useCallback(() => {
    authFetch<{ results: MyShort[] }>("/api/shorts/me")
      .then((d) => setShorts(d.results))
      .catch(() => setShorts([]));
  }, [authFetch]);

  useEffect(load, [load]);

  // Tant qu'une vidéo est en encodage, on rafraîchit la liste.
  useEffect(() => {
    if (!shorts?.some((s) => s.status === "processing" || s.status === "uploading")) return;
    const id = setInterval(load, 10_000);
    return () => clearInterval(id);
  }, [shorts, load]);

  async function pick(f: File | null) {
    setError(null);
    setFile(null);
    if (!f) return;
    if (!f.type.startsWith("video/")) {
      setError(t("shortsMgr.notVideo"));
      return;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(t("shortsMgr.tooBig", { n: MAX_SIZE_MB }));
      return;
    }
    const duration = await videoDuration(f);
    if (duration > MAX_DURATION_S + 0.5) {
      setError(t("shortsMgr.tooLong", { n: MAX_DURATION_S }));
      return;
    }
    setFile(f);
    if (!title) setTitle(f.name.replace(/\.[^.]+$/, "").slice(0, 120));
  }

  async function publish() {
    if (!file || !title.trim()) return;
    setError(null);
    setProgress(0);
    try {
      const res = await authFetch<CreateResp>("/api/shorts/me", {
        method: "POST",
        body: JSON.stringify({ title: title.trim() }),
      });
      if (res.upload.mode === "tus") {
        await tusUpload(file, res.upload, title.trim(), setProgress);
        await authFetch(`/api/shorts/me/${res.short.id}/uploaded`, { method: "POST" });
      }
      setTitle("");
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      load();
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setError(e.data?.detail ?? t("shortsMgr.uploadError"));
    } finally {
      setProgress(null);
    }
  }

  async function remove(id: number) {
    if (!window.confirm(t("shortsMgr.confirmDelete"))) return;
    try {
      await authFetch(`/api/shorts/me/${id}`, { method: "DELETE" });
      load();
    } catch {
      setError(t("shortsMgr.deleteError"));
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
      <section className="space-y-3 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
        <h2 className="font-semibold">{t("shortsMgr.title")}</h2>
        <p className="text-xs text-neutral-400">
          {t("shortsMgr.rules", { n: MAX_DURATION_S, mb: MAX_SIZE_MB })}
        </p>
        <input
          ref={inputRef}
          type="file"
          accept="video/*"
          onChange={(e) => pick(e.target.files?.[0] ?? null)}
          className="block w-full text-sm text-neutral-300 file:mr-3 file:rounded-lg file:border-0 file:bg-neutral-800 file:px-3 file:py-2 file:text-sm file:text-neutral-100 hover:file:bg-neutral-700"
        />
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={120}
          placeholder={t("shortsMgr.titlePlaceholder")}
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
        />
        {progress !== null && (
          <div className="h-2 overflow-hidden rounded-full bg-neutral-800" aria-live="polite">
            <div
              className="h-full bg-secondary transition-all"
              style={{ width: `${Math.round(progress * 100)}%` }}
            />
          </div>
        )}
        {error && <p className="text-sm text-red-300">{error}</p>}
        <button
          type="button"
          onClick={publish}
          disabled={!file || !title.trim() || progress !== null}
          className="w-full rounded-lg bg-secondary px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-secondary-light disabled:opacity-50"
        >
          {progress !== null
            ? t("shortsMgr.uploading", { pct: Math.round(progress * 100) })
            : t("shortsMgr.publish")}
        </button>
        <Link
          href="/instant"
          className="block text-center text-xs text-neutral-500 hover:text-neutral-300"
        >
          {t("shortsMgr.seeFeed")}
        </Link>
      </section>

      <section className="rounded-2xl border border-neutral-800 bg-neutral-900/60 p-5">
        <h2 className="mb-3 font-semibold">{t("shortsMgr.mine")}</h2>
        {shorts === null ? (
          <p className="text-sm text-neutral-500">{t("common.loading")}</p>
        ) : shorts.length === 0 ? (
          <p className="text-sm text-neutral-500">{t("shortsMgr.none")}</p>
        ) : (
          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
            {shorts.map((s) => (
              <li key={s.id} className="overflow-hidden rounded-xl border border-neutral-800">
                <div className="relative aspect-[9/16] bg-neutral-800">
                  {s.thumbnail_url && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={s.thumbnail_url} alt="" className="h-full w-full object-cover" />
                  )}
                  <span
                    className={`absolute left-2 top-2 rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                      s.status === "ready"
                        ? "bg-emerald-500 text-neutral-950"
                        : s.status === "failed"
                          ? "bg-red-500 text-white"
                          : "bg-amber-400 text-neutral-950"
                    }`}
                  >
                    {t(`shortsMgr.status.${s.status}`)}
                  </span>
                </div>
                <div className="space-y-1 p-2 text-xs">
                  <p className="line-clamp-1 font-semibold text-neutral-100">{s.title}</p>
                  <p className="text-neutral-500">
                    {date(s.created_at)} · {t("shorts.views", { n: num(s.view_count) })} · ♥{" "}
                    {num(s.like_count)}
                  </p>
                  {!s.is_published && (
                    <p className="text-amber-300">{t("shortsMgr.unpublished")}</p>
                  )}
                  <button
                    type="button"
                    onClick={() => remove(s.id)}
                    className="text-red-300 hover:underline"
                  >
                    {t("shortsMgr.delete")}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
