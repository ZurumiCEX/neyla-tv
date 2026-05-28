"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";

export default function AdminMessagesPage() {
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
      setStatus({ ok: true, msg: "Message envoyé." });
      setTitle("");
      setBody("");
    } catch (err) {
      const e = err as { data?: { detail?: string } };
      setStatus({ ok: false, msg: e.data?.detail ?? "Échec de l'envoi." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-xl">
      <h2 className="mb-2 text-lg font-bold">Message support / système</h2>
      <p className="mb-4 text-sm text-neutral-400">
        Envoie un message à un utilisateur. Il apparaît dans sa boîte de réception.
      </p>
      <form onSubmit={send} className="space-y-3">
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Nom d'utilisateur"
          required
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
        />
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Titre"
          required
          maxLength={120}
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
        />
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Message…"
          required
          rows={5}
          maxLength={2000}
          className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm text-neutral-100"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          {busy ? "Envoi…" : "Envoyer"}
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
