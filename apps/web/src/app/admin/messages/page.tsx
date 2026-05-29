"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useT } from "@/lib/i18n";

export default function AdminMessagesPage() {
  const t = useT();
  const { authFetch } = useAuth();
  const [username, setUsername] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setStatus(null);
    try {
      await authFetch("/api/admin/messages", {
        method: "POST",
        body: JSON.stringify({ username, title, body }),
      });
      setStatus({ ok: true, msg: t("admin.msg.sent") });
      setTitle("");
      setBody("");
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setStatus({ ok: false, msg: e.data?.detail ?? t("admin.msg.sendError") });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-xl rounded-2xl border border-neutral-800 bg-neutral-900/60 p-6">
      <h2 className="mb-2 text-lg font-bold">{t("admin.msg.title")}</h2>
      <p className="mb-4 text-sm text-neutral-400">{t("admin.msg.desc")}</p>
      <form onSubmit={send} className="space-y-3">
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder={t("admin.msg.username")}
          required
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
        />
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={t("admin.msg.msgTitle")}
          required
          maxLength={120}
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
        />
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder={t("admin.msg.body")}
          required
          rows={5}
          maxLength={2000}
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100 outline-none focus:border-secondary-light"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy ? t("admin.msg.sending") : t("admin.msg.send")}
        </button>
      </form>
      {status && (
        <p className={`mt-3 text-sm ${status.ok ? "text-emerald-300" : "text-red-300"}`}>
          {status.msg}
        </p>
      )}
    </div>
  );
}
